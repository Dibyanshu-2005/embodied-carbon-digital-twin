"""
Data Ingestion and Management Module.
Handles parsing and validation for Excel (.xlsx/.xls) and CSV files.
Provides automatic column mapping and handles missing optional fields gracefully.
Generates full calculation export workbooks and CSV reports.
"""

import io
import base64
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple

class DataManager:
    """Manages ingestion and export of construction carbon datasets."""

    @staticmethod
    def normalize_key(key: str) -> str:
        """Normalize dataframe column headers to snake_case standard."""
        return (
            str(key)
            .strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("(", "")
            .replace(")", "")
            .replace("/", "_")
            .replace(".", "")
        )

    @classmethod
    def parse_uploaded_file(cls, filename: str, file_bytes_or_b64: Any, current_state: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:
        """
        Parse an uploaded Excel or CSV file.
        Accepts raw bytes, BytesIO, or base64 encoded string.
        Returns (parsed_data_dict, success_message).
        """
        # Decode base64 if string
        if isinstance(file_bytes_or_b64, str):
            if "," in file_bytes_or_b64:
                file_bytes_or_b64 = file_bytes_or_b64.split(",", 1)[1]
            raw_bytes = base64.b64decode(file_bytes_or_b64)
        elif isinstance(file_bytes_or_b64, (bytes, bytearray)):
            raw_bytes = bytes(file_bytes_or_b64)
        elif hasattr(file_bytes_or_b64, "read"):
            raw_bytes = file_bytes_or_b64.read()
        else:
            raise ValueError("Unsupported file payload format.")

        lower_name = filename.lower()
        if lower_name.endswith(".xlsx") or lower_name.endswith(".xls"):
            return cls.parse_excel_bytes(raw_bytes, current_state)
        elif lower_name.endswith(".csv"):
            return cls.parse_csv_bytes(raw_bytes, current_state)
        else:
            raise ValueError("File must be an Excel spreadsheet (.xlsx, .xls) or CSV (.csv)")

    @classmethod
    def parse_excel_bytes(cls, raw_bytes: bytes, current_state: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:
        """Parse multi-sheet or single-sheet Excel workbook."""
        excel_file = io.BytesIO(raw_bytes)
        xls = pd.ExcelFile(excel_file, engine="openpyxl")
        sheet_names = [s.strip() for s in xls.sheet_names]
        
        state = current_state if current_state else {}
        project_meta = state.get("project_meta", {
            "project_name": "Imported Concrete Project",
            "concrete_volume_m3": 350.0,
            "concrete_grade": "M30",
            "carbon_budget_tonnes": 100.0
        })
        materials = state.get("materials", [])
        transport = state.get("transport", [])
        equipment = state.get("equipment", [])
        stages = state.get("stages", [])

        sheets_found = []

        for sheet in xls.sheet_names:
            clean_sheet = sheet.strip().lower()
            df = pd.read_excel(xls, sheet_name=sheet).dropna(how="all")
            if df.empty:
                continue

            # Standardize column headers
            col_map = {orig: cls.normalize_key(orig) for orig in df.columns}
            df_norm = df.rename(columns=col_map)

            if "meta" in clean_sheet or "project" in clean_sheet:
                # Meta sheet: can be Property-Value or single row
                if "property" in df_norm.columns and "value" in df_norm.columns:
                    meta_dict = dict(zip(df_norm["property"].astype(str), df_norm["value"]))
                    project_meta.update(meta_dict)
                else:
                    first_row = df_norm.iloc[0].to_dict()
                    project_meta.update(first_row)
                sheets_found.append("Project_Meta")

            elif "equipment" in clean_sheet:
                equipment = cls._process_equipment_dataframe(df_norm)
                sheets_found.append("Equipment")

            elif "transport" in clean_sheet:
                transport = cls._process_transport_dataframe(df_norm)
                sheets_found.append("Transport")

            elif "material" in clean_sheet:
                materials = cls._process_materials_dataframe(df_norm)
                sheets_found.append("Materials")

            elif "stage" in clean_sheet or "progress" in clean_sheet:
                stages = cls._process_stages_dataframe(df_norm)
                sheets_found.append("Stages")

            elif any("distance" in c for c in df_norm.columns):
                transport = cls._process_transport_dataframe(df_norm)
                sheets_found.append("Transport (detected)")

            elif any("fuel" in c or "hour" in c or "equipment" in c for c in df_norm.columns):
                equipment = cls._process_equipment_dataframe(df_norm)
                sheets_found.append("Equipment (detected)")

            elif any("consumed" in c or "material" in c for c in df_norm.columns):
                materials = cls._process_materials_dataframe(df_norm)
                sheets_found.append("Materials (detected)")

        if not sheets_found:
            # If sheet names didn't match, inspect first sheet
            first_sheet = xls.sheet_names[0]
            df_first = pd.read_excel(xls, sheet_name=first_sheet)
            col_map = {orig: cls.normalize_key(orig) for orig in df_first.columns}
            df_norm = df_first.rename(columns=col_map)
            materials = cls._process_materials_dataframe(df_norm)
            sheets_found.append(f"{first_sheet} (as Materials)")

        msg = f"Successfully parsed Excel workbook ({', '.join(sheets_found)})"
        return {
            "project_meta": project_meta,
            "materials": materials,
            "transport": transport,
            "equipment": equipment,
            "stages": stages
        }, msg

    @classmethod
    def parse_csv_bytes(cls, raw_bytes: bytes, current_state: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:
        """Parse standalone CSV file and intelligently map to the matching module."""
        csv_file = io.BytesIO(raw_bytes)
        df = pd.read_csv(csv_file).dropna(how="all")
        if df.empty:
            raise ValueError("The uploaded CSV file is empty.")

        col_map = {orig: cls.normalize_key(orig) for orig in df.columns}
        df_norm = df.rename(columns=col_map)

        state = current_state if current_state else {}
        project_meta = state.get("project_meta", {
            "project_name": "CSV Imported Project",
            "concrete_volume_m3": 350.0,
            "concrete_grade": "M30",
            "carbon_budget_tonnes": 100.0
        })
        materials = state.get("materials", [])
        transport = state.get("transport", [])
        equipment = state.get("equipment", [])
        stages = state.get("stages", [])

        cols = set(df_norm.columns)
        if any(c in cols for c in ["distance_km", "distance", "vehicle_type", "transport_ef"]):
            transport = cls._process_transport_dataframe(df_norm)
            msg = f"Imported {len(transport)} transport records from CSV."
        elif any(c in cols for c in ["equipment_name", "fuel_consumed", "hours_operated"]):
            equipment = cls._process_equipment_dataframe(df_norm)
            msg = f"Imported {len(equipment)} equipment records from CSV."
        elif any(c in cols for c in ["stage_id", "stage_name", "volume_m3", "status"]):
            stages = cls._process_stages_dataframe(df_norm)
            msg = f"Imported {len(stages)} construction stages from CSV."
        else:
            materials = cls._process_materials_dataframe(df_norm)
            msg = f"Imported {len(materials)} material records from CSV."

        return {
            "project_meta": project_meta,
            "materials": materials,
            "transport": transport,
            "equipment": equipment,
            "stages": stages
        }, msg

    @staticmethod
    def _process_materials_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Map generic columns to standard materials dictionary schema."""
        records = []
        for _, row in df.iterrows():
            name = row.get("material_name", row.get("material", row.get("name", "Material")))
            if pd.isna(name):
                continue

            category = row.get("category", "General")
            unit = row.get("unit", "kg")
            planned = row.get("planned_quantity", row.get("planned_qty", row.get("planned", 0.0)))
            delivered = row.get("delivered_quantity", row.get("delivered_qty", planned))
            consumed = row.get("consumed_quantity", row.get("consumed_qty", delivered))
            waste_pct = row.get("waste_percentage", row.get("waste_pct", row.get("waste", 0.0)))
            waste_qty = row.get("waste_quantity", row.get("waste_qty", 0.0))
            ef = row.get("emission_factor", row.get("ef", row.get("factor", 0.89)))
            source = row.get("ef_source", row.get("source", "Standard Reference"))

            records.append({
                "material_name": str(name).strip(),
                "category": str(category).strip() if pd.notna(category) else "General",
                "unit": str(unit).strip() if pd.notna(unit) else "kg",
                "planned_quantity": float(planned) if pd.notna(planned) else 0.0,
                "delivered_quantity": float(delivered) if pd.notna(delivered) else 0.0,
                "consumed_quantity": float(consumed) if pd.notna(consumed) else 0.0,
                "waste_percentage": float(waste_pct) if pd.notna(waste_pct) else 0.0,
                "waste_quantity": float(waste_qty) if pd.notna(waste_qty) else 0.0,
                "emission_factor": float(ef) if pd.notna(ef) else 0.0,
                "ef_source": str(source).strip() if pd.notna(source) else "Reference"
            })
        return records

    @staticmethod
    def _process_transport_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Map generic columns to standard transport dictionary schema."""
        records = []
        for _, row in df.iterrows():
            name = row.get("material_name", row.get("item", row.get("material", "Delivery")))
            if pd.isna(name):
                continue
            v_type = row.get("vehicle_type", row.get("vehicle", "Heavy Tipper Truck (16-32t)"))
            qty = row.get("quantity_transported", row.get("quantity", row.get("tonnes", 0.0)))
            unit = row.get("unit", "tonnes")
            dist = row.get("distance_km", row.get("distance", 0.0))
            rt = bool(row.get("round_trip", False))
            ef = row.get("transport_ef", row.get("emission_factor", 0.105))
            src = row.get("ef_source", row.get("source", "Standard Freight Factor"))

            records.append({
                "material_name": str(name).strip(),
                "vehicle_type": str(v_type).strip() if pd.notna(v_type) else "Heavy Truck",
                "quantity_transported": float(qty) if pd.notna(qty) else 0.0,
                "unit": str(unit).strip() if pd.notna(unit) else "tonnes",
                "distance_km": float(dist) if pd.notna(dist) else 0.0,
                "round_trip": rt,
                "transport_ef": float(ef) if pd.notna(ef) else 0.105,
                "ef_source": str(src).strip() if pd.notna(src) else "Reference"
            })
        return records

    @staticmethod
    def _process_equipment_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Map generic columns to standard equipment dictionary schema."""
        records = []
        for _, row in df.iterrows():
            name = row.get("equipment_name", row.get("name", "Equipment"))
            if pd.isna(name):
                continue
            cat = row.get("category", "Equipment")
            fuel_type = row.get("fuel_type", "Diesel")
            hours = row.get("hours_operated", row.get("operating_hours", 0.0))
            rate = row.get("fuel_consumption_rate", row.get("rate", 0.0))
            fuel_tot = row.get("fuel_consumed", row.get("energy_consumed", row.get("fuel", row.get("energy", 0.0))))
            ef = row.get("emission_factor", 2.68 if "diesel" in str(fuel_type).lower() else 0.716)
            notes = row.get("notes", "")

            records.append({
                "equipment_name": str(name).strip(),
                "category": str(cat).strip() if pd.notna(cat) else "Equipment",
                "fuel_type": str(fuel_type).strip() if pd.notna(fuel_type) else "Diesel",
                "hours_operated": float(hours) if pd.notna(hours) else 0.0,
                "fuel_consumption_rate": float(rate) if pd.notna(rate) else 0.0,
                "fuel_consumed": float(fuel_tot) if pd.notna(fuel_tot) else 0.0,
                "emission_factor": float(ef) if pd.notna(ef) else 2.68,
                "notes": str(notes) if pd.notna(notes) else ""
            })
        return records

    @staticmethod
    def _process_stages_dataframe(df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Map generic columns to standard stages dictionary schema."""
        records = []
        for idx, row in df.iterrows():
            stg_id = row.get("stage_id", idx + 1)
            name = row.get("name", row.get("stage_name", f"Stage {stg_id}"))
            date_val = str(row.get("date", "2025-01-01")).split("T")[0]
            vol = row.get("volume_m3", row.get("volume", 50.0))
            status = row.get("status", "Scheduled")
            desc = row.get("description", "")

            records.append({
                "stage_id": int(stg_id) if pd.notna(stg_id) else idx + 1,
                "name": str(name).strip(),
                "date": date_val,
                "volume_m3": float(vol) if pd.notna(vol) else 50.0,
                "status": str(status).strip() if pd.notna(status) else "Scheduled",
                "description": str(desc) if pd.notna(desc) else ""
            })
        return records

    @classmethod
    def export_project_to_excel(cls, twin_state: Dict[str, Any]) -> bytes:
        """Generate a multi-tab Excel calculation report."""
        summary = twin_state["summary"]
        benchmarks = twin_state["benchmarks"]
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            # 1. Executive Summary Sheet
            summary_data = [
                {"Metric": "Project Name", "Value": summary["project_name"]},
                {"Metric": "Concrete Volume (m³)", "Value": summary["concrete_volume_m3"]},
                {"Metric": "Concrete Grade", "Value": summary["concrete_grade"]},
                {"Metric": "Total Cumulative Embodied Carbon (tCO2e)", "Value": summary["total_emissions_tonnes"]},
                {"Metric": "Carbon Intensity (kgCO2e / m³)", "Value": summary["carbon_intensity_kg_per_m3"]},
                {"Metric": "Concrete Mix Classification", "Value": benchmarks.get("mix_category", "Blended Low-Carbon Mix")},
                {"Metric": "Conventional Baseline Savings", "Value": f"{benchmarks['savings_vs_conventional_pct']}% vs CPWD 2019"},
                {"Metric": "Target Carbon Budget (tCO2e)", "Value": summary["carbon_budget_tonnes"]},
                {"Metric": "Budget Variance Status", "Value": benchmarks["budget_status"]},
                {"Metric": "Savings vs Indian Conventional M30 Baseline (%)", "Value": f"{benchmarks['savings_vs_conventional_pct']}%"},
                {"Metric": "Module A1-A3 Materials (tCO2e)", "Value": summary["materials_module"]["total_emissions_tonnes"]},
                {"Metric": "Module A4 Transport to Site (tCO2e)", "Value": summary["transport_module"]["total_emissions_tonnes"]},
                {"Metric": "Module A5a Equipment & Plant (tCO2e)", "Value": summary["equipment_module"]["total_emissions_tonnes"]},
                {"Metric": "Wastage Carbon Embedded Penalty (tCO2e)", "Value": summary["waste_penalty_tonnes"]},
                {"Metric": "Rebar Reinforcement Intensity (kg steel / m³)", "Value": summary["rebar_intensity_kg_per_m3"]}
            ]
            pd.DataFrame(summary_data).to_excel(writer, sheet_name="Executive_Summary", index=False)

            # 2. Materials Sheet
            mat_items = summary["materials_module"]["items"]
            pd.DataFrame(mat_items).to_excel(writer, sheet_name="A1-A3_Materials", index=False)

            # 3. Transport Sheet
            tr_items = summary["transport_module"]["items"]
            pd.DataFrame(tr_items).to_excel(writer, sheet_name="A4_Transport", index=False)

            # 4. Equipment Sheet
            eq_items = summary["equipment_module"]["items"]
            pd.DataFrame(eq_items).to_excel(writer, sheet_name="A5a_Equipment", index=False)

            # 5. Timeline Stages Sheet
            stages_items = twin_state["timeline"]["stages"]
            pd.DataFrame(stages_items).to_excel(writer, sheet_name="Stages_Timeline", index=False)

            # 6. Snapshots / Version History
            if "snapshots" in twin_state and twin_state["snapshots"]:
                pd.DataFrame(twin_state["snapshots"]).to_excel(writer, sheet_name="Version_History", index=False)

        return output.getvalue()
