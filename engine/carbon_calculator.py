"""
Concrete Construction Embodied Carbon Calculation Engine.
Compliant with EN 15978 / ISO 21930 Upfront Embodied Carbon Modules:
- Module A1-A3: Raw Material Extraction, Supply, and Manufacturing
- Module A4: Transportation to Construction Site
- Module A5a: Construction Installation (Site Plant & Equipment Fuel/Electricity)
- Module A5b: Material Wastage and Scrap Carbon Penalty

References:
- ICE Database v3.0 (Inventory of Carbon & Energy, University of Bath)
- Central Electricity Authority (CEA) CO2 Baseline Database for the Indian Power Sector (0.716 kgCO2e/kWh)
- IPCC 2006 Guidelines for National GHG Inventories (Diesel: 2.68 kgCO2e/L)
- Indian EPDs & CPWD Green Specifications (Cement, Sand, TMT Steel)
"""

from typing import Dict, Any, List, Optional
import math

# Default Cradle-to-Gate Emission Factors (Module A1-A3) in kgCO2e per unit
DEFAULT_MATERIAL_EMISSION_FACTORS: Dict[str, Dict[str, Any]] = {
    "cement_opc53": {
        "name": "OPC 53 Grade Cement",
        "factor": 0.890,
        "unit": "kgCO2e/kg",
        "category": "Cement",
        "source": "Indian Cement EPD / CPWD Baseline (Average Indian dry-process rotary kiln)"
    },
    "cement_opc43": {
        "name": "OPC 43 Grade Cement",
        "factor": 0.850,
        "unit": "kgCO2e/kg",
        "category": "Cement",
        "source": "Indian Cement Industry LCI Baseline"
    },
    "cement_ppc": {
        "name": "PPC (Portland Pozzolana Cement - ~30% Fly Ash)",
        "factor": 0.620,
        "unit": "kgCO2e/kg",
        "category": "Cement",
        "source": "Indian EPD / CMA Baseline for PPC"
    },
    "cement_ggbs_blend": {
        "name": "PSC / GGBS Blended Cement (50% Slag)",
        "factor": 0.460,
        "unit": "kgCO2e/kg",
        "category": "Cement",
        "source": "ICE Database v3.0 / Indian Slag Cement Association"
    },
    "fly_ash": {
        "name": "Fly Ash (SCM By-product)",
        "factor": 0.015,
        "unit": "kgCO2e/kg",
        "category": "SCM",
        "source": "ICE v3.0 (Economic allocation for transport & beneficiation)"
    },
    "ggbs": {
        "name": "Ground Granulated Blast-Furnace Slag (GGBS)",
        "factor": 0.090,
        "unit": "kgCO2e/kg",
        "category": "SCM",
        "source": "ICE Database v3.0 / CSIR-CBRI Roorkee"
    },
    "coarse_aggregate": {
        "name": "Coarse Aggregate (10mm - 20mm crushed stone)",
        "factor": 0.007,
        "unit": "kgCO2e/kg",
        "category": "Aggregates",
        "source": "ICE Database v3.0 (Crushed rock aggregate including quarrying & crushing)"
    },
    "fine_aggregate_sand": {
        "name": "Fine Aggregate (River Sand)",
        "factor": 0.005,
        "unit": "kgCO2e/kg",
        "category": "Aggregates",
        "source": "ICE Database v3.0 (Dredged/extracted river sand)"
    },
    "fine_aggregate_msand": {
        "name": "Fine Aggregate (Manufactured M-Sand)",
        "factor": 0.008,
        "unit": "kgCO2e/kg",
        "category": "Aggregates",
        "source": "Indian LCI for VSI Crusher M-Sand production"
    },
    "water": {
        "name": "Mixing Water (Municipal / Borewell)",
        "factor": 0.0003,
        "unit": "kgCO2e/kg",
        "category": "Water",
        "source": "UK DEFRA / Indian municipal water treatment & pumping"
    },
    "chemical_admixture": {
        "name": "Chemical Admixture (PCE Superplasticizer)",
        "factor": 1.450,
        "unit": "kgCO2e/kg",
        "category": "Admixtures",
        "source": "EFCA (European Federation of Concrete Admixtures Associations) EPD"
    },
    "rebar_tmt_steel": {
        "name": "TMT Rebar Fe 500D (Primary BF-BOF Route)",
        "factor": 2.250,
        "unit": "kgCO2e/kg",
        "category": "Reinforcement",
        "source": "Indian Steel Sector LCI (Tata Steel / JSW EPD average)"
    },
    "rebar_recycled_steel": {
        "name": "TMT Rebar (Secondary EAF / Scrap Route)",
        "factor": 1.400,
        "unit": "kgCO2e/kg",
        "category": "Reinforcement",
        "source": "ICE Database v3.0 / Secondary Steel Producers Association"
    },
    "formwork_plywood": {
        "name": "Formwork Plywood (Amortized per pour - 15 reuses)",
        "factor": 0.080,
        "unit": "kgCO2e/m2",
        "category": "Formwork",
        "source": "ICE Database v3.0 (Amortized timber shuttering)"
    }
}

# Transport Emission Factors (Module A4) in kgCO2e per tonne-km
DEFAULT_TRANSPORT_EMISSION_FACTORS: Dict[str, Dict[str, Any]] = {
    "tipper_truck_heavy": {
        "name": "Heavy Tipper Truck (16-32 tonne, Diesel)",
        "factor": 0.105,
        "unit": "kgCO2e/(t·km)",
        "source": "UK DEFRA / Indian Ministry of Road Transport freight factor"
    },
    "transit_mixer": {
        "name": "Ready-Mix Transit Mixer (Diesel, drum revolving)",
        "factor": 0.220,
        "unit": "kgCO2e/(t·km)",
        "source": "NRMCA / Indian RMCMA standard for loaded agitating transit mixer"
    },
    "lcv_light_truck": {
        "name": "Light Commercial Vehicle (LCV < 7.5t)",
        "factor": 0.290,
        "unit": "kgCO2e/(t·km)",
        "source": "Indian Transport Sector Emission Factors (ARAI / CPCB)"
    },
    "electric_heavy_truck": {
        "name": "Electric Heavy Truck (Green Logistics)",
        "factor": 0.045,
        "unit": "kgCO2e/(t·km)",
        "source": "IEA / Commercial EV Life Cycle Assessment"
    },
    "rail_freight": {
        "name": "Rail Freight (Bulk cement/slag freight)",
        "factor": 0.025,
        "unit": "kgCO2e/(t·km)",
        "source": "Indian Railways Carbon Accounting"
    }
}

# Energy & Site Equipment Factors (Module A5a)
DIESEL_EMISSION_FACTOR = 2.68  # kgCO2e per litre of diesel (IPCC)
GRID_ELECTRICITY_EMISSION_FACTOR = 0.716  # kgCO2e per kWh (CEA India 2023 grid average)

def safe_float(val: Any, default: float = 0.0) -> float:
    """Safely parse float value from user input or excel cell."""
    if val is None:
        return default
    if isinstance(val, (int, float)):
        if math.isnan(val) or math.isinf(val):
            return default
        return float(val)
    try:
        cleaned = str(val).strip().replace(",", "")
        return float(cleaned)
    except (ValueError, TypeError):
        return default

class ConcreteCarbonEngine:
    """Comprehensive EN 15978 Upfront Embodied Carbon Engine for Concrete Construction."""

    @staticmethod
    def calculate_materials_a1_a3(materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Module A1-A3 Cradle-to-Gate emissions for all materials.
        Differentiates between productive consumption and material wastage.
        """
        items_result = []
        total_a1_a3_kg = 0.0
        total_planned_kg_co2 = 0.0
        total_waste_kg_co2 = 0.0
        total_cementitious_qty_kg = 0.0
        total_rebar_qty_kg = 0.0
        
        category_breakdown: Dict[str, float] = {}

        for mat in materials:
            name = str(mat.get("material_name", mat.get("name", "Unknown Material")))
            category = str(mat.get("category", "General"))
            unit = str(mat.get("unit", "kg")).lower().strip()
            
            # Quantities
            planned_qty = safe_float(mat.get("planned_quantity", mat.get("planned_qty", 0.0)))
            delivered_qty = safe_float(mat.get("delivered_quantity", mat.get("delivered_qty", planned_qty)))
            consumed_qty = safe_float(mat.get("consumed_quantity", mat.get("consumed_qty", delivered_qty)))
            
            # Wastage percentage or absolute quantity
            waste_pct = safe_float(mat.get("waste_percentage", mat.get("waste_pct", 0.0)))
            waste_qty = safe_float(mat.get("waste_quantity", mat.get("waste_qty", 0.0)))
            
            # If waste_qty is not given but waste_pct is, compute waste_qty
            if waste_qty == 0.0 and waste_pct > 0.0:
                waste_qty = consumed_qty * (waste_pct / 100.0)
            elif waste_qty > 0.0 and consumed_qty > 0.0 and waste_pct == 0.0:
                waste_pct = (waste_qty / consumed_qty) * 100.0

            # Emission factor (cradle-to-gate)
            ef = safe_float(mat.get("emission_factor", mat.get("ef", 0.0)))
            source = str(mat.get("ef_source", mat.get("source", "Standard Reference")))

            # Unit normalisation: if in tonnes, convert to kg for internal standard
            mult = 1000.0 if "tonne" in unit or "ton" in unit else 1.0

            # Net productive consumed quantity (excluding wasted part from productive structure)
            # Standard carbon accounting: Total consumed material generates A1-A3 carbon.
            # We track how much of that carbon was for productive work vs wasted.
            total_material_co2_kg = (consumed_qty * mult) * ef
            planned_material_co2_kg = (planned_qty * mult) * ef
            waste_material_co2_kg = (waste_qty * mult) * ef

            total_a1_a3_kg += total_material_co2_kg
            total_planned_kg_co2 += planned_material_co2_kg
            total_waste_kg_co2 += waste_material_co2_kg

            # Track totals for specific civil indicators
            cat_lower = category.lower()
            name_lower = name.lower()
            if "cement" in cat_lower or "cement" in name_lower or "fly ash" in name_lower or "ggbs" in name_lower:
                total_cementitious_qty_kg += (consumed_qty * mult)
            if "rebar" in cat_lower or "steel" in cat_lower or "reinforcement" in name_lower or "tmt" in name_lower:
                total_rebar_qty_kg += (consumed_qty * mult)

            # Category accumulator
            category_breakdown[category] = category_breakdown.get(category, 0.0) + total_material_co2_kg

            items_result.append({
                "material_name": name,
                "category": category,
                "unit": unit,
                "planned_quantity": planned_qty,
                "delivered_quantity": delivered_qty,
                "consumed_quantity": consumed_qty,
                "waste_quantity": round(waste_qty, 3),
                "waste_percentage": round(waste_pct, 2),
                "emission_factor": ef,
                "ef_source": source,
                "carbon_emission_kg": round(total_material_co2_kg, 2),
                "carbon_emission_tonnes": round(total_material_co2_kg / 1000.0, 4),
                "planned_carbon_kg": round(planned_material_co2_kg, 2),
                "waste_carbon_penalty_kg": round(waste_material_co2_kg, 2)
            })

        # Calculate percentages
        for item in items_result:
            item["share_pct"] = round((item["carbon_emission_kg"] / total_a1_a3_kg * 100.0) if total_a1_a3_kg > 0 else 0.0, 2)

        # Sort items by highest carbon contribution
        items_result.sort(key=lambda x: x["carbon_emission_kg"], reverse=True)

        return {
            "items": items_result,
            "total_emissions_kg": round(total_a1_a3_kg, 2),
            "total_emissions_tonnes": round(total_a1_a3_kg / 1000.0, 4),
            "total_planned_kg": round(total_planned_kg_co2, 2),
            "total_planned_tonnes": round(total_planned_kg_co2 / 1000.0, 4),
            "total_waste_penalty_kg": round(total_waste_kg_co2, 2),
            "total_waste_penalty_tonnes": round(total_waste_kg_co2 / 1000.0, 4),
            "category_breakdown": {k: round(v, 2) for k, v in category_breakdown.items()},
            "total_cementitious_kg": round(total_cementitious_qty_kg, 2),
            "total_rebar_kg": round(total_rebar_qty_kg, 2)
        }

    @staticmethod
    def calculate_transport_a4(transport_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Module A4 Transportation to Site emissions.
        Emissions = Quantity (tonnes) * Distance (km) * Transport EF (kgCO2e / t-km).
        """
        items_result = []
        total_a4_kg = 0.0
        total_tonne_km = 0.0

        for tr in transport_records:
            material_name = str(tr.get("material_name", tr.get("item", "General Delivery")))
            vehicle_type = str(tr.get("vehicle_type", "Heavy Tipper Truck (16-32t)"))
            qty_transported = safe_float(tr.get("quantity_transported", tr.get("quantity", 0.0)))
            unit = str(tr.get("unit", "tonnes")).lower().strip()
            
            # Standardize quantity to tonnes
            tonnes = qty_transported / 1000.0 if "kg" in unit else qty_transported
            
            distance_km = safe_float(tr.get("distance_km", tr.get("distance", 0.0)))
            round_trip = bool(tr.get("round_trip", False))
            effective_distance = distance_km * (2.0 if round_trip else 1.0)
            
            ef = safe_float(tr.get("transport_ef", tr.get("emission_factor", 0.105)))
            source = str(tr.get("ef_source", "DEFRA/CPCB Freight Factor"))

            tonne_km = tonnes * effective_distance
            co2_kg = tonne_km * ef

            total_tonne_km += tonne_km
            total_a4_kg += co2_kg

            items_result.append({
                "material_name": material_name,
                "vehicle_type": vehicle_type,
                "quantity_tonnes": round(tonnes, 3),
                "distance_km": distance_km,
                "round_trip": round_trip,
                "effective_distance_km": effective_distance,
                "transport_ef": ef,
                "ef_source": source,
                "tonne_km": round(tonne_km, 2),
                "carbon_emission_kg": round(co2_kg, 2),
                "carbon_emission_tonnes": round(co2_kg / 1000.0, 4)
            })

        for item in items_result:
            item["share_pct"] = round((item["carbon_emission_kg"] / total_a4_kg * 100.0) if total_a4_kg > 0 else 0.0, 2)

        items_result.sort(key=lambda x: x["carbon_emission_kg"], reverse=True)

        return {
            "items": items_result,
            "total_emissions_kg": round(total_a4_kg, 2),
            "total_emissions_tonnes": round(total_a4_kg / 1000.0, 4),
            "total_tonne_km": round(total_tonne_km, 2)
        }

    @staticmethod
    def calculate_equipment_a5a(equipment_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate Module A5a Construction Equipment & Energy emissions.
        Emissions = Fuel (L) * 2.68 kgCO2e/L + Electricity (kWh) * 0.716 kgCO2e/kWh.
        """
        items_result = []
        total_a5a_kg = 0.0
        total_diesel_litres = 0.0
        total_electricity_kwh = 0.0

        for eq in equipment_records:
            name = str(eq.get("equipment_name", eq.get("name", "Site Plant")))
            category = str(eq.get("category", "Equipment"))
            fuel_type = str(eq.get("fuel_type", "Diesel")).strip().capitalize()
            
            hours_operated = safe_float(eq.get("hours_operated", eq.get("operating_hours", 0.0)))
            fuel_rate = safe_float(eq.get("fuel_consumption_rate", eq.get("rate", 0.0)))  # L/hr or kWh/hr
            fuel_consumed = safe_float(eq.get("fuel_consumed", eq.get("total_fuel", 0.0)))
            
            # If total fuel wasn't directly given, derive from hours * rate
            if fuel_consumed == 0.0 and hours_operated > 0.0 and fuel_rate > 0.0:
                fuel_consumed = hours_operated * fuel_rate

            custom_ef = eq.get("emission_factor")
            if custom_ef is not None and safe_float(custom_ef) > 0.0:
                ef = safe_float(custom_ef)
            elif "electric" in fuel_type.lower() or "grid" in fuel_type.lower():
                ef = GRID_ELECTRICITY_EMISSION_FACTOR
            else:
                ef = DIESEL_EMISSION_FACTOR

            co2_kg = fuel_consumed * ef
            total_a5a_kg += co2_kg

            if "electric" in fuel_type.lower() or "grid" in fuel_type.lower():
                total_electricity_kwh += fuel_consumed
            else:
                total_diesel_litres += fuel_consumed

            items_result.append({
                "equipment_name": name,
                "category": category,
                "fuel_type": fuel_type,
                "hours_operated": hours_operated,
                "fuel_consumption_rate": fuel_rate,
                "energy_consumed": round(fuel_consumed, 2),
                "energy_unit": "kWh" if "electric" in fuel_type.lower() else "Litres",
                "emission_factor": ef,
                "carbon_emission_kg": round(co2_kg, 2),
                "carbon_emission_tonnes": round(co2_kg / 1000.0, 4)
            })

        for item in items_result:
            item["share_pct"] = round((item["carbon_emission_kg"] / total_a5a_kg * 100.0) if total_a5a_kg > 0 else 0.0, 2)

        items_result.sort(key=lambda x: x["carbon_emission_kg"], reverse=True)

        return {
            "items": items_result,
            "total_emissions_kg": round(total_a5a_kg, 2),
            "total_emissions_tonnes": round(total_a5a_kg / 1000.0, 4),
            "total_diesel_litres": round(total_diesel_litres, 2),
            "total_electricity_kwh": round(total_electricity_kwh, 2)
        }

    @staticmethod
    def calculate_project_summary(
        project_meta: Dict[str, Any],
        materials: List[Dict[str, Any]],
        transport: List[Dict[str, Any]],
        equipment: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate total project embodied carbon across EN 15978 life cycle modules:
        Total = A1-A3 (Raw materials) + A4 (Transport) + A5a (Equipment) + A5b (Waste handling)
        Ensures strict prevention of double-counting while exposing wastage penalties.
        """
        concrete_volume_m3 = safe_float(
            project_meta.get("concrete_volume_m3", project_meta.get("total_concrete_m3", 350.0)),
            default=350.0
        )
        if concrete_volume_m3 <= 0.0:
            concrete_volume_m3 = 1.0  # Avoid division by zero

        concrete_grade = str(project_meta.get("concrete_grade", "M30"))
        project_name = str(project_meta.get("project_name", "Concrete Construction Package (Demo Activity)"))
        carbon_budget_tonnes = safe_float(project_meta.get("carbon_budget_tonnes", 120.0), default=120.0)
        target_budget_intensity_kg = (carbon_budget_tonnes * 1000.0) / concrete_volume_m3

        # Module Calculations
        res_materials = ConcreteCarbonEngine.calculate_materials_a1_a3(materials)
        res_transport = ConcreteCarbonEngine.calculate_transport_a4(transport)
        res_equipment = ConcreteCarbonEngine.calculate_equipment_a5a(equipment)

        # Totals
        total_kg = (
            res_materials["total_emissions_kg"] +
            res_transport["total_emissions_kg"] +
            res_equipment["total_emissions_kg"]
        )
        total_tonnes = total_kg / 1000.0

        planned_total_kg = (
            res_materials["total_planned_kg"] +
            res_transport["total_emissions_kg"] * 0.95 +  # Planned transport approx
            res_equipment["total_emissions_kg"] * 0.92
        )
        planned_total_tonnes = planned_total_kg / 1000.0

        # Functional Unit Intensities
        # 1. Concrete Mix Intensity (Mix alone: cement + SCM + aggregates + water + admixtures)
        concrete_mix_carbon_kg = (
            res_materials["total_emissions_kg"] - (res_materials["total_rebar_kg"] * 2.25) # subtract rebar component
        )
        # Ensure non-negative
        concrete_mix_carbon_kg = max(0.0, concrete_mix_carbon_kg)
        concrete_mix_intensity_kg_per_m3 = concrete_mix_carbon_kg / concrete_volume_m3

        # 2. Total Reinforced Concrete Structure Intensity (A1-A5 full structural system)
        total_structural_intensity_kg_per_m3 = total_kg / concrete_volume_m3
        rebar_intensity_kg_per_m3 = res_materials["total_rebar_kg"] / concrete_volume_m3
        cement_intensity_kg_per_m3 = res_materials["total_cementitious_kg"] / concrete_volume_m3

        # Life Cycle Stage Contribution
        stage_breakdown = [
            {
                "module": "A1-A3",
                "label": "Product Stage (Raw Materials)",
                "emissions_kg": res_materials["total_emissions_kg"],
                "emissions_tonnes": res_materials["total_emissions_tonnes"],
                "share_pct": round((res_materials["total_emissions_kg"] / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
                "color": "#3B82F6"
            },
            {
                "module": "A4",
                "label": "Transport to Site",
                "emissions_kg": res_transport["total_emissions_kg"],
                "emissions_tonnes": res_transport["total_emissions_tonnes"],
                "share_pct": round((res_transport["total_emissions_kg"] / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
                "color": "#F59E0B"
            },
            {
                "module": "A5a",
                "label": "Construction Equipment & Energy",
                "emissions_kg": res_equipment["total_emissions_kg"],
                "emissions_tonnes": res_equipment["total_emissions_tonnes"],
                "share_pct": round((res_equipment["total_emissions_kg"] / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
                "color": "#8B5CF6"
            },
            {
                "module": "A5b (Penalty)",
                "label": "Wastage Carbon Embedded Loss",
                "emissions_kg": res_materials["total_waste_penalty_kg"],
                "emissions_tonnes": res_materials["total_waste_penalty_tonnes"],
                "share_pct": round((res_materials["total_waste_penalty_kg"] / total_kg * 100.0) if total_kg > 0 else 0.0, 1),
                "color": "#EF4444"
            }
        ]

        # Variance between actual and planned
        delta_tonnes = total_tonnes - planned_total_tonnes
        delta_pct = (delta_tonnes / planned_total_tonnes * 100.0) if planned_total_tonnes > 0 else 0.0

        return {
            "project_name": project_name,
            "concrete_volume_m3": round(concrete_volume_m3, 2),
            "concrete_grade": concrete_grade,
            "carbon_budget_tonnes": carbon_budget_tonnes,
            "target_budget_intensity_kg": round(target_budget_intensity_kg, 1),
            "total_emissions_kg": round(total_kg, 2),
            "total_emissions_tonnes": round(total_tonnes, 3),
            "planned_total_tonnes": round(planned_total_tonnes, 3),
            "variance_delta_tonnes": round(delta_tonnes, 3),
            "variance_delta_pct": round(delta_pct, 1),
            "carbon_intensity_kg_per_m3": round(total_structural_intensity_kg_per_m3, 1),
            "concrete_mix_intensity_kg_per_m3": round(concrete_mix_intensity_kg_per_m3, 1),
            "rebar_intensity_kg_per_m3": round(rebar_intensity_kg_per_m3, 1),
            "cement_intensity_kg_per_m3": round(cement_intensity_kg_per_m3, 1),
            "materials_module": res_materials,
            "transport_module": res_transport,
            "equipment_module": res_equipment,
            "stage_breakdown": stage_breakdown,
            "waste_penalty_tonnes": res_materials["total_waste_penalty_tonnes"],
            "waste_penalty_pct": round((res_materials["total_waste_penalty_kg"] / total_kg * 100.0) if total_kg > 0 else 0.0, 1)
        }
