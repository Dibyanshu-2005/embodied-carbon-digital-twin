"""
Dynamic Digital Twin State & Timeline Management Module.
Maintains the digital representation of the physical concrete construction activity:
- Stage-by-stage construction progress
- S-Curve timeline (Planned vs Actual Cumulative vs Projected)
- Version history & snapshots
- What-if branch simulations
- 3D structural twin geometry & hotspot mapping
"""

import copy
import datetime
from typing import Dict, Any, List, Optional
from engine.carbon_calculator import ConcreteCarbonEngine, safe_float
from engine.benchmarks import evaluate_benchmarks

class ConcreteDigitalTwin:
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        self.snapshots: List[Dict[str, Any]] = []
        if initial_data:
            self.load_state(initial_data, snapshot_label="Initial State Ingestion")
        else:
            self.reset_to_default()

    def reset_to_default(self):
        """Initialize with realistic concrete construction activity dataset."""
        from sample_data.generate_samples import get_default_project_data
        default_data = get_default_project_data()
        self.load_state(default_data, snapshot_label="System Default (Demo Activity)")

    def load_state(self, data: Dict[str, Any], snapshot_label: str = "State Updated"):
        """Load full project state and recalculate all twin metrics."""
        self.project_meta = copy.deepcopy(data.get("project_meta", {
            "project_name": "Concrete Construction Package (Demo Activity)",
            "concrete_volume_m3": 420.0,
            "concrete_grade": "M30 Design Mix",
            "carbon_budget_tonnes": 115.0,
            "start_date": "2025-01-10",
            "end_date": "2025-06-30"
        }))
        self.materials = copy.deepcopy(data.get("materials", []))
        self.transport = copy.deepcopy(data.get("transport", []))
        self.equipment = copy.deepcopy(data.get("equipment", []))
        self.stages = copy.deepcopy(data.get("stages", []))

        total_vol = safe_float(self.project_meta.get("concrete_volume_m3", 420.0))
        # Ensure each stage has its materials, transport, and equipment
        for s in self.stages:
            vol = safe_float(s.get("volume_m3", 0.0))
            ratio = (vol / total_vol) if total_vol > 0 else 0.2
            if "materials" not in s:
                s_mats = copy.deepcopy(self.materials)
                for m in s_mats:
                    m["consumed_quantity"] = round(safe_float(m.get("consumed_quantity", 0.0)) * ratio, 2)
                    m["planned_quantity"] = round(safe_float(m.get("planned_quantity", m["consumed_quantity"])) * ratio, 2)
                s["materials"] = s_mats
            if "transport" not in s:
                s_trans = copy.deepcopy(self.transport)
                for t in s_trans:
                    t["quantity_transported"] = round(safe_float(t.get("quantity_transported", 0.0)) * ratio, 2)
                s["transport"] = s_trans
            if "equipment" not in s:
                s_equip = copy.deepcopy(self.equipment)
                for e in s_equip:
                    if "hours_operated" in e:
                        e["hours_operated"] = round(safe_float(e.get("hours_operated", 0.0)) * ratio, 1)
                    if "fuel_consumed" in e:
                        e["fuel_consumed"] = round(safe_float(e.get("fuel_consumed", 0.0)) * ratio, 1)
                s["equipment"] = s_equip

        self.active_stage_id = self.stages[0]["stage_id"] if self.stages else 1
        if self.stages:
            self.materials = copy.deepcopy(self.stages[0]["materials"])
            self.transport = copy.deepcopy(self.stages[0]["transport"])
            self.equipment = copy.deepcopy(self.stages[0]["equipment"])

        self.recalculate()
        self.create_snapshot(label=snapshot_label, author="System")

    def _calculate_stage_emissions(self, stg: Dict[str, Any]) -> float:
        """Calculate total emissions in tonnes for a single stage's materials, transport, and equipment."""
        mats = stg.get("materials", [])
        trans = stg.get("transport", [])
        equip = stg.get("equipment", [])
        if hasattr(self, "active_stage_id") and stg.get("stage_id") == self.active_stage_id:
            mats = self.materials
            trans = self.transport
            equip = self.equipment
        if not mats and not trans and not equip:
            return 0.0
        r_m = ConcreteCarbonEngine.calculate_materials_a1_a3(mats)
        r_t = ConcreteCarbonEngine.calculate_transport_a4(trans)
        r_e = ConcreteCarbonEngine.calculate_equipment_a5a(equip)
        return round((r_m["total_emissions_kg"] + r_t["total_emissions_kg"] + r_e["total_emissions_kg"]) / 1000.0, 3)

    def select_stage(self, stage_id: int) -> bool:
        """Switch active stage in digital twin and synchronize its materials, transport, and equipment."""
        stg = next((s for s in self.stages if s.get("stage_id") == stage_id), None)
        if not stg:
            return False

        # Save current active stage's items first
        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["materials"] = copy.deepcopy(self.materials)
                curr["transport"] = copy.deepcopy(self.transport)
                curr["equipment"] = copy.deepcopy(self.equipment)

        self.active_stage_id = stage_id
        if "materials" not in stg:
            stg["materials"] = []
        if "transport" not in stg:
            stg["transport"] = []
        if "equipment" not in stg:
            stg["equipment"] = []

        self.materials = copy.deepcopy(stg["materials"])
        self.transport = copy.deepcopy(stg["transport"])
        self.equipment = copy.deepcopy(stg["equipment"])
        self.recalculate()
        return True

    def recalculate(self):
        """Run calculation engine and update digital twin state."""
        self.summary = ConcreteCarbonEngine.calculate_project_summary(
            self.project_meta,
            self.materials,
            self.transport,
            self.equipment
        )

        # Refresh dynamic timeline progress across all stages
        self.timeline_data = self._compute_timeline_progress()

        # Update summary totals to reflect the project's real cumulative progress to date
        cum_carbon = self.timeline_data.get("current_cumulative_carbon_tonnes", 0.0)
        if cum_carbon > 0.0:
            self.summary["total_emissions_tonnes"] = cum_carbon
            self.summary["total_emissions_kg"] = round(cum_carbon * 1000.0, 1)
            comp_vol = self.timeline_data.get("completed_volume_m3", self.summary["concrete_volume_m3"])
            if comp_vol > 0:
                self.summary["concrete_mix_intensity_kg_per_m3"] = round(self.summary["total_emissions_kg"] / comp_vol, 1)
            self.summary["carbon_intensity_kg_per_m3"] = round(self.summary["total_emissions_kg"] / max(1.0, self.summary["concrete_volume_m3"]), 1)

        # Evaluate concrete mix against published benchmarks (LETI & CPWD)
        budget_target_kg = (self.summary["carbon_budget_tonnes"] * 1000.0) / self.summary["concrete_volume_m3"]
        self.benchmarks = evaluate_benchmarks(
            actual_intensity_kg_per_m3=self.summary["concrete_mix_intensity_kg_per_m3"],
            project_budget_kg_per_m3=budget_target_kg
        )

        # Refresh 3D structural twin elements
        self.structural_elements = self._generate_structural_twin_elements()

    def update_material(self, index: int, updates: Dict[str, Any], reason: str = "Material Parameter Updated"):
        """Update a specific material's parameters and recalculate."""
        if 0 <= index < len(self.materials):
            self.materials[index].update(updates)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["materials"] = copy.deepcopy(self.materials)
            self.recalculate()
            self.create_snapshot(label=f"{reason} ({self.materials[index].get('material_name')})", author="User")
            return True
        return False

    def update_transport(self, index: int, updates: Dict[str, Any], reason: str = "Transport Parameter Updated"):
        """Update transport record and recalculate."""
        if 0 <= index < len(self.transport):
            self.transport[index].update(updates)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["transport"] = copy.deepcopy(self.transport)
            self.recalculate()
            self.create_snapshot(label=f"{reason} ({self.transport[index].get('material_name')})", author="User")
            return True
        return False

    def update_equipment(self, index: int, updates: Dict[str, Any], reason: str = "Equipment Parameter Updated"):
        """Update equipment record and recalculate."""
        if 0 <= index < len(self.equipment):
            self.equipment[index].update(updates)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["equipment"] = copy.deepcopy(self.equipment)
            self.recalculate()
            self.create_snapshot(label=f"{reason} ({self.equipment[index].get('equipment_name')})", author="User")
            return True
        return False

    def update_project_meta(self, updates: Dict[str, Any]):
        """Update project-level metadata such as budget or total volume."""
        cleaned = {}
        for k, v in updates.items():
            if k in ("concrete_volume_m3", "carbon_budget_tonnes"):
                cleaned[k] = safe_float(v)
            else:
                cleaned[k] = v
        self.project_meta.update(cleaned)
        self.recalculate()
        self.create_snapshot(label="Project Metadata Updated", author="User")

    def add_periodic_stage(self, stage_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new periodic site log milestone with continuous duration tracking.
        Automatically calculates duration as the continuous interval between the new date
        and the previous recorded date so there are no time gaps.
        """
        prev_date_str = None
        if self.stages:
            prev_date_str = self.stages[-1].get("date")

        new_id = len(self.stages) + 1
        new_date_str = stage_data.get("date", datetime.date.today().isoformat())
        
        # Calculate continuous duration
        duration_days = 0
        if prev_date_str:
            try:
                d1 = datetime.date.fromisoformat(prev_date_str)
                d2 = datetime.date.fromisoformat(new_date_str)
                duration_days = max(1, (d2 - d1).days)
            except Exception:
                duration_days = 30

        # Save currently active stage's items before creating new stage
        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["materials"] = copy.deepcopy(self.materials)
                curr["transport"] = copy.deepcopy(self.transport)
                curr["equipment"] = copy.deepcopy(self.equipment)

        copy_prev = stage_data.get("copy_previous", True)
        if isinstance(copy_prev, str):
            copy_prev = (copy_prev.lower() not in ("false", "0", "fresh"))
        elif not isinstance(copy_prev, bool):
            copy_prev = bool(copy_prev)

        if copy_prev and self.stages:
            prev_stg = self.stages[-1]
            new_materials = copy.deepcopy(prev_stg.get("materials", self.materials))
            new_transport = copy.deepcopy(prev_stg.get("transport", self.transport))
            new_equipment = copy.deepcopy(prev_stg.get("equipment", self.equipment))
        else:
            # START FRESH, BLANK LOG (User adds materials one by one)
            new_materials = []
            new_transport = []
            new_equipment = []

        new_stage = {
            "stage_id": new_id,
            "name": stage_data.get("name", f"Site Milestone Pour #{new_id}"),
            "date": new_date_str,
            "volume_m3": safe_float(stage_data.get("volume_m3", 50.0)),
            "status": stage_data.get("status", "In Progress"),
            "description": stage_data.get("description", f"Continuous site progress ({duration_days} days interval)"),
            "duration_days": duration_days,
            "materials": new_materials,
            "transport": new_transport,
            "equipment": new_equipment
        }
        self.stages.append(new_stage)

        # Activate the new stage
        self.active_stage_id = new_id
        self.materials = new_materials
        self.transport = new_transport
        self.equipment = new_equipment

        self.recalculate()
        self.create_snapshot(
            label=f"Logged Periodic Progress: {new_stage['name']} ({duration_days} days)",
            author=stage_data.get("author", "Project Manager")
        )
        return new_stage

    def add_material(self, mat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new material entry to the materials log using central database defaults."""
        from engine.emission_database import find_material_factor
        mat_name = mat_data.get("material_name", "Custom Construction Material")
        db_item = find_material_factor(mat_name)
        
        category = mat_data.get("category") or (db_item["category"] if db_item else "General")
        unit = mat_data.get("unit") or (db_item["unit"] if db_item else "kg")
        ef = safe_float(mat_data.get("emission_factor") or (db_item["emission_factor"] if db_item else 0.50))
        source_code = mat_data.get("ef_source") or (db_item["source_code"] if db_item else "[1]")
        consumed_qty = safe_float(mat_data.get("consumed_quantity", 1000.0))
        planned_qty = safe_float(mat_data.get("planned_quantity", consumed_qty))
        waste_pct = safe_float(mat_data.get("waste_percentage", 3.0))
        waste_qty = round(consumed_qty * (waste_pct / 100.0), 3)

        new_mat = {
            "material_name": mat_name,
            "category": category,
            "unit": unit,
            "planned_quantity": planned_qty,
            "delivered_quantity": consumed_qty + waste_qty,
            "consumed_quantity": consumed_qty,
            "waste_percentage": waste_pct,
            "waste_quantity": waste_qty,
            "emission_factor": ef,
            "ef_source": source_code
        }
        self.materials.append(new_mat)
        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["materials"] = copy.deepcopy(self.materials)
                if curr.get("status") == "Scheduled":
                    curr["status"] = "In Progress"
        self.recalculate()
        self.create_snapshot(label=f"Added Material: {mat_name}", author=mat_data.get("author", "Project Manager"))
        return new_mat

    def add_materials_batch(self, materials_list: List[Dict[str, Any]], snapshot_label: str = "Batch Material Ingestion") -> int:
        """Add a batch of material items at once, synchronizing with active stage and recalculating once."""
        from engine.emission_database import find_material_factor
        added_count = 0
        for mat_data in materials_list:
            mat_name = mat_data.get("material_name", "Custom Construction Material")
            db_item = find_material_factor(mat_name)
            category = mat_data.get("category") or (db_item["category"] if db_item else "General")
            unit = mat_data.get("unit") or (db_item["unit"] if db_item else "kg")
            ef = safe_float(mat_data.get("emission_factor") or (db_item["emission_factor"] if db_item else 0.50))
            source_code = mat_data.get("ef_source") or (db_item["source_code"] if db_item else "[1]")
            consumed_qty = safe_float(mat_data.get("consumed_quantity", 1000.0))
            planned_qty = safe_float(mat_data.get("planned_quantity", consumed_qty))
            waste_pct = safe_float(mat_data.get("waste_percentage", 3.0))
            waste_qty = round(consumed_qty * (waste_pct / 100.0), 3)

            new_mat = {
                "material_name": mat_name,
                "category": category,
                "unit": unit,
                "planned_quantity": planned_qty,
                "delivered_quantity": consumed_qty + waste_qty,
                "consumed_quantity": consumed_qty,
                "waste_percentage": waste_pct,
                "waste_quantity": waste_qty,
                "emission_factor": ef,
                "ef_source": source_code
            }
            self.materials.append(new_mat)
            added_count += 1

        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["materials"] = copy.deepcopy(self.materials)
                if curr.get("status") == "Scheduled":
                    curr["status"] = "In Progress"

        self.recalculate()
        self.create_snapshot(label=snapshot_label, author="Project Manager")
        return added_count

    def delete_material(self, index: int) -> bool:
        """Remove a material entry by index."""
        if 0 <= index < len(self.materials):
            self.materials.pop(index)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["materials"] = copy.deepcopy(self.materials)
            self.recalculate()
            return True
        return False

    def delete_transport(self, index: int) -> bool:
        """Remove a transport haulage entry by index."""
        if 0 <= index < len(self.transport):
            self.transport.pop(index)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["transport"] = copy.deepcopy(self.transport)
            self.recalculate()
            return True
        return False

    def delete_equipment(self, index: int) -> bool:
        """Remove an equipment plant entry by index."""
        if 0 <= index < len(self.equipment):
            self.equipment.pop(index)
            if hasattr(self, "active_stage_id") and self.active_stage_id:
                curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
                if curr:
                    curr["equipment"] = copy.deepcopy(self.equipment)
            self.recalculate()
            return True
        return False

    def delete_stage(self, stage_id: int) -> bool:
        """Remove a site progress log milestone by stage_id."""
        initial_len = len(self.stages)
        self.stages = [s for s in self.stages if s.get("stage_id") != stage_id]
        if len(self.stages) < initial_len:
            # Re-index remaining stages 1..N
            for i, stg in enumerate(self.stages, 1):
                stg["stage_id"] = i
            if hasattr(self, "active_stage_id") and self.stages:
                target_id = self.stages[0]["stage_id"]
                self.select_stage(target_id)
            else:
                self.recalculate()
            return True
        return False

    def update_stage_status(self, stage_id: int, status: str) -> bool:
        """Update a site progress log milestone's status ('Completed', 'In Progress', 'Scheduled') and recalculate."""
        stg = next((s for s in self.stages if s.get("stage_id") == stage_id), None)
        if not stg:
            return False
        stg["status"] = status
        self.recalculate()
        self.create_snapshot(label=f"Updated Log #{stage_id} status to {status}", author="Project Manager")
        return True

    def add_transport(self, tr_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new haulage transport entry."""
        from engine.emission_database import find_transport_factor
        v_type = tr_data.get("vehicle_type", "Heavy Tipper Truck (16-32t)")
        db_item = find_transport_factor(v_type)

        ef = safe_float(tr_data.get("transport_ef") or (db_item["emission_factor"] if db_item else 0.105))
        source_code = tr_data.get("ef_source") or (db_item["source_code"] if db_item else "[6]")
        qty = safe_float(tr_data.get("quantity_transported", 20.0))
        dist = safe_float(tr_data.get("distance_km", 50.0))

        new_tr = {
            "material_name": tr_data.get("material_name", "General Materials Haulage"),
            "vehicle_type": v_type,
            "quantity_transported": qty,
            "unit": tr_data.get("unit", "tonnes"),
            "distance_km": dist,
            "round_trip": bool(tr_data.get("round_trip", False)),
            "transport_ef": ef,
            "ef_source": source_code
        }
        self.transport.append(new_tr)
        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["transport"] = copy.deepcopy(self.transport)
        self.recalculate()
        self.create_snapshot(label=f"Added Transport: {new_tr['material_name']}", author="Project Manager")
        return new_tr

    def add_equipment(self, eq_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add a new plant & site equipment entry."""
        from engine.emission_database import find_equipment_factor
        eq_name = eq_data.get("equipment_name", "Site Equipment Plant")
        db_item = find_equipment_factor(eq_name)

        fuel_type = eq_data.get("fuel_type") or (db_item["fuel_type"] if db_item else "Diesel")
        ef = safe_float(eq_data.get("emission_factor") or (db_item["emission_factor"] if db_item else 2.68))
        hours = safe_float(eq_data.get("hours_operated", 40.0))
        fuel_cons = safe_float(eq_data.get("fuel_consumed", 100.0))

        new_eq = {
            "equipment_name": eq_name,
            "category": eq_data.get("category", "Construction Plant"),
            "fuel_type": fuel_type,
            "hours_operated": hours,
            "fuel_consumption_rate": round(fuel_cons / max(1.0, hours), 2),
            "fuel_consumed": fuel_cons,
            "emission_factor": ef,
            "notes": eq_data.get("notes", "Periodic plant telemetry")
        }
        self.equipment.append(new_eq)
        if hasattr(self, "active_stage_id") and self.active_stage_id:
            curr = next((s for s in self.stages if s.get("stage_id") == self.active_stage_id), None)
            if curr:
                curr["equipment"] = copy.deepcopy(self.equipment)
        self.recalculate()
        self.create_snapshot(label=f"Added Equipment: {eq_name}", author="Project Manager")
        return new_eq

    def simulate_what_if(self, modifications: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate a what-if scenario without committing changes to actual state.
        Allows instant evaluation of carbon reduction interventions:
        - SCM substitution (e.g. OPC -> PPC / GGBS)
        - Transport haulage reduction (e.g. local quarry)
        - Wastage reduction (e.g. BBS rebar optimization)
        - Green equipment electrification
        """
        sim_materials = copy.deepcopy(self.materials)
        sim_transport = copy.deepcopy(self.transport)
        sim_equipment = copy.deepcopy(self.equipment)
        sim_meta = copy.deepcopy(self.project_meta)

        # Apply substitutions
        if "cement_replacement_pct" in modifications:
            # Replace a percentage of OPC cement with GGBS or Fly Ash
            replacement_pct = safe_float(modifications["cement_replacement_pct"]) / 100.0
            scm_type = modifications.get("scm_type", "fly_ash")
            scm_ef = 0.015 if scm_type == "fly_ash" else 0.090  # GGBS

            for mat in sim_materials:
                if "opc" in mat.get("material_name", "").lower() or "cement" in mat.get("material_name", "").lower():
                    orig_qty = safe_float(mat.get("consumed_quantity", 0.0))
                    orig_ef = safe_float(mat.get("emission_factor", 0.89))
                    # Blended emission factor
                    blended_ef = (orig_ef * (1.0 - replacement_pct)) + (scm_ef * replacement_pct)
                    mat["emission_factor"] = round(blended_ef, 4)
                    mat["material_name"] = f"{mat['material_name']} ({int(replacement_pct*100)}% {scm_type.upper()} Blend)"

        if "transport_distance_multiplier" in modifications:
            # E.g. 0.6 to simulate local sourcing (40% distance reduction)
            mult = safe_float(modifications["transport_distance_multiplier"], 1.0)
            for tr in sim_transport:
                tr["distance_km"] = round(safe_float(tr.get("distance_km", 0.0)) * mult, 1)

        if "waste_reduction_pct" in modifications:
            # E.g. cut wastage in half
            waste_factor = 1.0 - (safe_float(modifications["waste_reduction_pct"]) / 100.0)
            for mat in sim_materials:
                mat["waste_percentage"] = round(safe_float(mat.get("waste_percentage", 0.0)) * waste_factor, 2)
                mat["waste_quantity"] = round(safe_float(mat.get("waste_quantity", 0.0)) * waste_factor, 3)

        if "electric_equipment" in modifications and modifications["electric_equipment"]:
            # Switch diesel pump / plant to grid electric
            for eq in sim_equipment:
                if eq.get("fuel_type", "").lower() == "diesel":
                    eq["fuel_type"] = "Electric (Grid)"
                    # Equivalent electrical energy: 1L diesel ~ 3.5 kWh mechanical useful work
                    litres = safe_float(eq.get("fuel_consumed", 0.0))
                    kwh = litres * 3.5
                    eq["fuel_consumed"] = round(kwh, 2)
                    eq["emission_factor"] = 0.716

        sim_summary = ConcreteCarbonEngine.calculate_project_summary(
            sim_meta, sim_materials, sim_transport, sim_equipment
        )
        sim_benchmarks = evaluate_benchmarks(
            sim_summary["concrete_mix_intensity_kg_per_m3"],
            (sim_meta.get("carbon_budget_tonnes", 120.0) * 1000.0) / sim_summary["concrete_volume_m3"]
        )

        carbon_saved_tonnes = self.summary["total_emissions_tonnes"] - sim_summary["total_emissions_tonnes"]
        carbon_saved_pct = (carbon_saved_tonnes / self.summary["total_emissions_tonnes"] * 100.0) if self.summary["total_emissions_tonnes"] > 0 else 0.0

        return {
            "baseline_summary": self.summary,
            "simulated_summary": sim_summary,
            "simulated_benchmarks": sim_benchmarks,
            "carbon_saved_tonnes": round(carbon_saved_tonnes, 3),
            "carbon_saved_pct": round(carbon_saved_pct, 1),
            "intensity_reduction_kg_per_m3": round(self.summary["carbon_intensity_kg_per_m3"] - sim_summary["carbon_intensity_kg_per_m3"], 1),
            "new_mix_category": sim_benchmarks["mix_category"],
            "new_mix_color": sim_benchmarks["mix_color"],
            "new_leti_band": sim_benchmarks["leti_band"],
            "new_leti_color": sim_benchmarks["leti_color"]
        }

    def _compute_timeline_progress(self) -> Dict[str, Any]:
        """
        Build historical timeline and S-Curve progression across construction stages.
        Guarantees that cumulative emissions strictly accumulate without fictitious drops.
        """
        stages = copy.deepcopy(self.stages)
        if not stages:
            # Fallback default 5-stage concrete sequence
            stages = [
                {"stage_id": 1, "name": "Substructure Footings & Raft", "date": "2025-01-20", "volume_m3": 110.0, "status": "Completed"},
                {"stage_id": 2, "name": "Plinth Beams & Columns to GF", "date": "2025-02-15", "volume_m3": 75.0, "status": "Completed"},
                {"stage_id": 3, "name": "First Floor Slab & Beams", "date": "2025-03-25", "volume_m3": 95.0, "status": "Completed"},
                {"stage_id": 4, "name": "Second Floor Columns & Slab", "date": "2025-04-30", "volume_m3": 85.0, "status": "In Progress"},
                {"stage_id": 5, "name": "Terrace Roof Slab & Parapet", "date": "2025-06-15", "volume_m3": 55.0, "status": "Scheduled"}
            ]

        total_vol = safe_float(self.project_meta.get("concrete_volume_m3", 420.0))
        budget_tonnes = safe_float(self.project_meta.get("carbon_budget_tonnes", 115.0))
        planned_total_carbon_tonnes = budget_tonnes

        cum_actual_vol = 0.0
        cum_actual_carbon = 0.0
        cum_planned_carbon = 0.0
        
        timeline_points = []
        completed_vol = 0.0

        for stg in stages:
            vol = safe_float(stg.get("volume_m3", 0.0))
            vol_share = (vol / total_vol) if total_vol > 0 else 0.2
            
            # Planned carbon fraction follows standard S-curve distribution
            stage_planned_carbon = planned_total_carbon_tonnes * vol_share
            cum_planned_carbon += stage_planned_carbon

            status = stg.get("status", "Scheduled")
            is_completed = status == "Completed"
            is_in_progress = status == "In Progress"

            stage_emissions = self._calculate_stage_emissions(stg)

            if is_completed:
                stage_actual_carbon = stage_emissions
                cum_actual_carbon += stage_actual_carbon
                cum_actual_vol += vol
                completed_vol += vol
                actual_point_carbon = round(cum_actual_carbon, 3)
                projected_point_carbon = None
            elif is_in_progress:
                stage_actual_carbon = stage_emissions
                if stg.get("stage_id") == 4 and not stg.get("is_custom", False) and stage_emissions > 0:
                    cum_actual_carbon += stage_actual_carbon * 0.5
                else:
                    cum_actual_carbon += stage_actual_carbon
                cum_actual_vol += vol * 0.5
                completed_vol += vol * 0.5
                actual_point_carbon = round(cum_actual_carbon, 3)
                projected_point_carbon = round(cum_actual_carbon, 3)
            else: # Scheduled
                actual_point_carbon = None
                intensity_rate = (cum_actual_carbon / cum_actual_vol) if cum_actual_vol > 0 else (budget_tonnes / total_vol)
                projected_point_carbon = round(cum_actual_carbon + (intensity_rate * max(0.0, total_vol - cum_actual_vol)), 3)

            timeline_points.append({
                "stage_id": stg.get("stage_id", len(timeline_points) + 1),
                "stage_name": stg.get("name", "Stage"),
                "date": stg.get("date", "2025-01-01"),
                "status": status,
                "volume_m3": vol,
                "stage_carbon_t": stage_emissions,
                "planned_cumulative_carbon_t": round(cum_planned_carbon, 3),
                "actual_cumulative_carbon_t": actual_point_carbon,
                "projected_cumulative_carbon_t": projected_point_carbon or actual_point_carbon,
                "progress_pct": round((completed_vol / total_vol * 100.0) if total_vol > 0 else 0.0, 1)
            })

        # Compute continuous duration between consecutive dates without gaps
        prev_date = None
        for pt in timeline_points:
            cur_date_str = pt.get("date", "")
            try:
                cur_date = datetime.date.fromisoformat(cur_date_str)
                if prev_date is not None:
                    delta_days = max(1, (cur_date - prev_date).days)
                    pt["duration_days"] = delta_days
                    pt["duration_label"] = f"{delta_days} days (since {prev_date.isoformat()})"
                else:
                    pt["duration_days"] = 0
                    pt["duration_label"] = "Initial Log Baseline"
                prev_date = cur_date
            except Exception:
                pt["duration_days"] = 0
                pt["duration_label"] = "—"

        overall_progress_pct = round((completed_vol / total_vol * 100.0) if total_vol > 0 else 0.0, 1)
        intensity_burn = (cum_actual_carbon / cum_actual_vol) if cum_actual_vol > 0 else (budget_tonnes / total_vol)
        final_projected = cum_actual_carbon + (intensity_burn * max(0.0, total_vol - cum_actual_vol))

        return {
            "stages": timeline_points,
            "overall_progress_pct": overall_progress_pct,
            "completed_volume_m3": round(completed_vol, 2),
            "remaining_volume_m3": round(max(0.0, total_vol - completed_vol), 2),
            "current_cumulative_carbon_tonnes": round(cum_actual_carbon, 3),
            "final_projected_carbon_tonnes": round(final_projected, 3)
        }

    def _generate_structural_twin_elements(self) -> List[Dict[str, Any]]:
        """
        Generate parametric 3D structural twin building elements:
        Footings, Columns, Plinth Beams, Slabs for 3-story concrete frame.
        Maps real carbon intensity & status to each physical member.
        """
        elements = []
        base_intensity = self.summary["carbon_intensity_kg_per_m3"]

        # 1. Foundation Footings (4 Isolated Footings + Central Raft)
        footing_coords = [
            {"id": "F1", "name": "Footing F1 (Corner NW)", "x": -4, "y": -0.5, "z": -4, "w": 2.2, "h": 0.8, "d": 2.2, "vol": 3.8, "status": "Completed", "stage": "Substructure"},
            {"id": "F2", "name": "Footing F2 (Corner NE)", "x": 4, "y": -0.5, "z": -4, "w": 2.2, "h": 0.8, "d": 2.2, "vol": 3.8, "status": "Completed", "stage": "Substructure"},
            {"id": "F3", "name": "Footing F3 (Corner SW)", "x": -4, "y": -0.5, "z": 4, "w": 2.2, "h": 0.8, "d": 2.2, "vol": 3.8, "status": "Completed", "stage": "Substructure"},
            {"id": "F4", "name": "Footing F4 (Corner SE)", "x": 4, "y": -0.5, "z": 4, "w": 2.2, "h": 0.8, "d": 2.2, "vol": 3.8, "status": "Completed", "stage": "Substructure"},
            {"id": "RAFT", "name": "Core Lift Raft Slab", "x": 0, "y": -0.6, "z": 0, "w": 3.6, "h": 1.0, "d": 3.6, "vol": 12.9, "status": "Completed", "stage": "Substructure"}
        ]
        for f in footing_coords:
            # Footings typically have lower rebar ratio, slightly lower intensity
            intensity = round(base_intensity * 0.92, 1)
            elements.append({
                **f,
                "type": "footing",
                "carbon_intensity_kg_m3": intensity,
                "total_carbon_kg": round(f["vol"] * intensity, 1),
                "leti_band": evaluate_benchmarks(intensity)["leti_band"]
            })

        # 2. Ground Floor Columns (4 Perimeter + 2 Core)
        col_coords = [
            {"id": "C_GF_1", "name": "Col GF-1", "x": -4, "y": 1.5, "z": -4, "w": 0.5, "h": 3.0, "d": 0.5, "vol": 0.75, "status": "Completed", "stage": "GF Structure"},
            {"id": "C_GF_2", "name": "Col GF-2", "x": 4, "y": 1.5, "z": -4, "w": 0.5, "h": 3.0, "d": 0.5, "vol": 0.75, "status": "Completed", "stage": "GF Structure"},
            {"id": "C_GF_3", "name": "Col GF-3", "x": -4, "y": 1.5, "z": 4, "w": 0.5, "h": 3.0, "d": 0.5, "vol": 0.75, "status": "Completed", "stage": "GF Structure"},
            {"id": "C_GF_4", "name": "Col GF-4", "x": 4, "y": 1.5, "z": 4, "w": 0.5, "h": 3.0, "d": 0.5, "vol": 0.75, "status": "Completed", "stage": "GF Structure"},
            {"id": "C_GF_CORE1", "name": "Core Col GF-5", "x": -1.2, "y": 1.5, "z": 0, "w": 0.6, "h": 3.0, "d": 0.6, "vol": 1.08, "status": "Completed", "stage": "GF Structure"},
            {"id": "C_GF_CORE2", "name": "Core Col GF-6", "x": 1.2, "y": 1.5, "z": 0, "w": 0.6, "h": 3.0, "d": 0.6, "vol": 1.08, "status": "Completed", "stage": "GF Structure"}
        ]
        for c in col_coords:
            # Columns have heavy steel reinforcement (~160 kg/m3) -> higher carbon intensity
            intensity = round(base_intensity * 1.15, 1)
            elements.append({
                **c,
                "type": "column",
                "carbon_intensity_kg_m3": intensity,
                "total_carbon_kg": round(c["vol"] * intensity, 1),
                "leti_band": evaluate_benchmarks(intensity)["leti_band"]
            })

        # 3. First Floor Slab & Perimeter Beams
        slab_1 = {
            "id": "SLAB_L1",
            "name": "Level 1 Suspended Post-Tensioned Slab",
            "x": 0, "y": 3.1, "z": 0,
            "w": 10.5, "h": 0.25, "d": 10.5,
            "vol": 27.5,
            "status": "Completed",
            "stage": "Level 1 Slab",
            "type": "slab",
            "carbon_intensity_kg_m3": round(base_intensity * 0.98, 1),
            "total_carbon_kg": round(27.5 * base_intensity * 0.98, 1),
            "leti_band": evaluate_benchmarks(base_intensity * 0.98)["leti_band"]
        }
        elements.append(slab_1)

        # 4. First Floor Columns
        col_l1_coords = [
            {"id": "C_L1_1", "name": "Col L1-1", "x": -4, "y": 4.7, "z": -4, "w": 0.45, "h": 3.0, "d": 0.45, "vol": 0.61, "status": "In Progress", "stage": "Level 2 Structure"},
            {"id": "C_L1_2", "name": "Col L1-2", "x": 4, "y": 4.7, "z": -4, "w": 0.45, "h": 3.0, "d": 0.45, "vol": 0.61, "status": "In Progress", "stage": "Level 2 Structure"},
            {"id": "C_L1_3", "name": "Col L1-3", "x": -4, "y": 4.7, "z": 4, "w": 0.45, "h": 3.0, "d": 0.45, "vol": 0.61, "status": "In Progress", "stage": "Level 2 Structure"},
            {"id": "C_L1_4", "name": "Col L1-4", "x": 4, "y": 4.7, "z": 4, "w": 0.45, "h": 3.0, "d": 0.45, "vol": 0.61, "status": "In Progress", "stage": "Level 2 Structure"}
        ]
        for c in col_l1_coords:
            intensity = round(base_intensity * 1.12, 1)
            elements.append({
                **c,
                "type": "column",
                "carbon_intensity_kg_m3": intensity,
                "total_carbon_kg": round(c["vol"] * intensity, 1),
                "leti_band": evaluate_benchmarks(intensity)["leti_band"]
            })

        # 5. Roof Terrace Slab (Scheduled)
        slab_roof = {
            "id": "SLAB_ROOF",
            "name": "Terrace Roof Slab & Parapets",
            "x": 0, "y": 6.3, "z": 0,
            "w": 10.5, "h": 0.22, "d": 10.5,
            "vol": 24.2,
            "status": "Scheduled",
            "stage": "Terrace Roof",
            "type": "slab",
            "carbon_intensity_kg_m3": round(base_intensity * 0.95, 1),
            "total_carbon_kg": round(24.2 * base_intensity * 0.95, 1),
            "leti_band": evaluate_benchmarks(base_intensity * 0.95)["leti_band"]
        }
        elements.append(slab_roof)

        return elements

    def create_snapshot(self, label: str, author: str = "User") -> Dict[str, Any]:
        """Save an immutable version snapshot of the digital twin."""
        snapshot = {
            "snapshot_id": f"v{len(self.snapshots) + 1}",
            "label": label,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "author": author,
            "total_emissions_tonnes": self.summary["total_emissions_tonnes"],
            "carbon_intensity_kg_m3": self.summary["carbon_intensity_kg_per_m3"],
            "mix_category": self.benchmarks["mix_category"],
            "leti_band": self.benchmarks["leti_band"],
            "waste_penalty_tonnes": self.summary["waste_penalty_tonnes"],
            "materials_count": len(self.materials),
            "progress_pct": self.timeline_data["overall_progress_pct"]
        }
        self.snapshots.append(snapshot)
        return snapshot

    def get_full_state(self) -> Dict[str, Any]:
        """Return the comprehensive digital twin representation."""
        return {
            "project_meta": self.project_meta,
            "materials": self.materials,
            "transport": self.transport,
            "equipment": self.equipment,
            "stages": self.stages,
            "summary": self.summary,
            "benchmarks": self.benchmarks,
            "timeline": self.timeline_data,
            "structural_twin": {
                "elements": self.structural_elements,
                "total_elements": len(self.structural_elements)
            },
            "snapshots": self.snapshots
        }
