"""
Sample Dataset Generator for Concrete Construction Embodied Carbon Monitoring.
Generates real-world civil engineering datasets based on the Mahindra Eden / GKSPL Whole Life Carbon Study:
- Multi-sheet Excel workbook (.xlsx)
- Individual CSV files for Materials, Transport, Equipment, and Stages
- Blank Excel template for user uploads
- Verified Mahindra Eden carbon baseline comparison files
"""

import os
import shutil
import pandas as pd
from typing import Dict, Any

def get_default_project_data() -> Dict[str, Any]:
    """Returns the real-world concrete construction activity dataset from Mahindra Eden / GKSPL Study."""
    project_meta = {
        "project_name": "Mahindra Eden - Whole Life Carbon Study",
        "contractor": "Mahindra Lifespaces / GKSPL",
        "location": "Bengaluru, Karnataka, India",
        "concrete_volume_m3": 55480.98,
        "concrete_grade": "M30 Design Mix",
        "carbon_budget_tonnes": 31311.61,  # Verified upfront baseline total (A1-A5)
        "start_date": "2023-01-01",
        "target_completion_date": "2025-05-31"
    }

    materials = [
        {
            "material_name": "Ready Mix Concrete (M30)",
            "category": "Concrete",
            "unit": "m3",
            "planned_quantity": 55480.98,
            "delivered_quantity": 55480.98,
            "consumed_quantity": 55480.98,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 273.683,
            "ef_source": "GKSPL Whole Life Carbon Study"
        },
        {
            "material_name": "Reinforcement Steel",
            "category": "Steel",
            "unit": "kg",
            "planned_quantity": 5125165.42,
            "delivered_quantity": 5125165.42,
            "consumed_quantity": 5125165.42,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 2.397,
            "ef_source": "GKSPL Whole Life Carbon Study"
        },
        {
            "material_name": "Solid Concrete Blocks",
            "category": "Masonry",
            "unit": "m3",
            "planned_quantity": 2348.95,
            "delivered_quantity": 2348.95,
            "consumed_quantity": 2348.95,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 188.450,
            "ef_source": "GKSPL Whole Life Carbon Study"
        },
        {
            "material_name": "Plastering",
            "category": "Finishing",
            "unit": "m3",
            "planned_quantity": 214.47,
            "delivered_quantity": 214.47,
            "consumed_quantity": 214.47,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 0.996,
            "ef_source": "GKSPL reference factor - cement proxy; not product-specific"
        },
        {
            "material_name": "Gypsum Punning",
            "category": "Finishing",
            "unit": "m2",
            "planned_quantity": 1261.15,
            "delivered_quantity": 1261.15,
            "consumed_quantity": 1261.15,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 0.0,
            "ef_source": "GKSPL BOQ; factor unavailable"
        },
        {
            "material_name": "uPVC Doors and Windows",
            "category": "Finishing",
            "unit": "m2",
            "planned_quantity": 13510.74,
            "delivered_quantity": 13510.74,
            "consumed_quantity": 13510.74,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 0.0,
            "ef_source": "GKSPL BOQ; factor unavailable"
        },
        {
            "material_name": "Timber",
            "category": "Finishing",
            "unit": "m2",
            "planned_quantity": 6570.93,
            "delivered_quantity": 6570.93,
            "consumed_quantity": 6570.93,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 0.0,
            "ef_source": "GKSPL BOQ; factor unavailable"
        },
        {
            "material_name": "XPS Insulation",
            "category": "Insulation",
            "unit": "m2",
            "planned_quantity": 4043.00,
            "delivered_quantity": 4043.00,
            "consumed_quantity": 4043.00,
            "waste_percentage": 0.0,
            "waste_quantity": 0.0,
            "emission_factor": 0.0,
            "ef_source": "GKSPL BOQ; factor unavailable"
        }
    ]

    transport = [
        {
            "material_name": "Ready Mix Concrete (M30)",
            "vehicle_type": "Heavy Duty Vehicle",
            "quantity_transported": 0.0,
            "unit": "m3",
            "distance_km": 0.0,
            "round_trip": False,
            "transport_ef": 0.0,
            "ef_source": "GKSPL; actual trip data unavailable"
        },
        {
            "material_name": "Reinforcement Steel",
            "vehicle_type": "Heavy Duty Vehicle",
            "quantity_transported": 0.0,
            "unit": "kg",
            "distance_km": 0.0,
            "round_trip": False,
            "transport_ef": 0.0,
            "ef_source": "GKSPL; actual trip data unavailable"
        },
        {
            "material_name": "Solid Concrete Blocks",
            "vehicle_type": "Medium Duty Vehicle",
            "quantity_transported": 0.0,
            "unit": "m3",
            "distance_km": 0.0,
            "round_trip": False,
            "transport_ef": 0.0,
            "ef_source": "GKSPL; actual trip data unavailable"
        }
    ]

    equipment = [
        {
            "equipment_name": "Concrete Pump",
            "category": "Concrete Placement",
            "fuel_type": "Diesel",
            "hours_operated": 0.0,
            "fuel_consumption_rate": 0.0,
            "fuel_consumed": 0.0,
            "emission_factor": 0.0,
            "notes": "Equipment-level records unavailable; A5 aggregate reported by Mahindra (698.68 tCO2e)"
        },
        {
            "equipment_name": "Tower Crane",
            "category": "Material Handling",
            "fuel_type": "Electricity",
            "hours_operated": 0.0,
            "fuel_consumption_rate": 0.0,
            "fuel_consumed": 0.0,
            "emission_factor": 0.0,
            "notes": "Equipment-level records unavailable"
        },
        {
            "equipment_name": "Transit Mixer",
            "category": "Concrete Transport",
            "fuel_type": "Diesel",
            "hours_operated": 0.0,
            "fuel_consumption_rate": 0.0,
            "fuel_consumed": 0.0,
            "emission_factor": 0.0,
            "notes": "Equipment-level records unavailable"
        },
        {
            "equipment_name": "Excavator",
            "category": "Earthwork",
            "fuel_type": "Diesel",
            "hours_operated": 0.0,
            "fuel_consumption_rate": 0.0,
            "fuel_consumed": 0.0,
            "emission_factor": 0.0,
            "notes": "Equipment-level records unavailable"
        },
        {
            "equipment_name": "DG Set",
            "category": "Power Generation",
            "fuel_type": "Diesel",
            "hours_operated": 0.0,
            "fuel_consumption_rate": 0.0,
            "fuel_consumed": 0.0,
            "emission_factor": 0.0,
            "notes": "Equipment-level records unavailable"
        }
    ]

    # Progressive site construction timeline across 5 stages (summing to 55,480.98 m3 total)
    stages = [
        {
            "stage_id": 1,
            "name": "Foundation",
            "date": "2023-01-01",
            "volume_m3": 14000.0,
            "status": "Completed",
            "description": "Construction stage; actual pour dates and quantities unavailable"
        },
        {
            "stage_id": 2,
            "name": "Substructure",
            "date": "2023-02-01",
            "volume_m3": 11000.0,
            "status": "Completed",
            "description": "Construction stage; actual pour dates and quantities unavailable"
        },
        {
            "stage_id": 3,
            "name": "Superstructure",
            "date": "2023-03-01",
            "volume_m3": 25000.0,
            "status": "Completed",
            "description": "Construction stage; actual pour dates and quantities unavailable"
        },
        {
            "stage_id": 4,
            "name": "Masonry",
            "date": "2023-04-01",
            "volume_m3": 3480.98,
            "status": "In Progress",
            "description": "Construction stage; actual quantities unavailable"
        },
        {
            "stage_id": 5,
            "name": "Finishing",
            "date": "2023-05-01",
            "volume_m3": 2000.0,
            "status": "Scheduled",
            "description": "Construction stage; actual quantities unavailable"
        }
    ]

    return {
        "project_meta": project_meta,
        "materials": materials,
        "transport": transport,
        "equipment": equipment,
        "stages": stages
    }

def generate_sample_files(base_dir: str = "/Users/rajat74/Desktop/C-Project/BTP"):
    """Creates sample Excel, CSV, and blank template files on disk."""
    data = get_default_project_data()

    sample_dir = os.path.join(base_dir, "sample_data")
    template_dir = os.path.join(base_dir, "static", "templates")
    os.makedirs(sample_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)

    # 1. Generate Multi-Sheet Excel File
    excel_path = os.path.join(sample_dir, "Concrete_Construction_Log.xlsx")
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_meta = pd.DataFrame([data["project_meta"]]).T.reset_index()
        df_meta.columns = ["Property", "Value"]
        df_meta.to_excel(writer, sheet_name="Project_Meta", index=False)

        df_mat = pd.DataFrame(data["materials"])
        df_mat.to_excel(writer, sheet_name="Materials", index=False)

        df_tr = pd.DataFrame(data["transport"])
        df_tr.to_excel(writer, sheet_name="Transport", index=False)

        df_eq = pd.DataFrame(data["equipment"])
        df_eq.to_excel(writer, sheet_name="Equipment", index=False)

        df_stg = pd.DataFrame(data["stages"])
        df_stg.to_excel(writer, sheet_name="Stages", index=False)

    shutil.copy(excel_path, os.path.join(sample_dir, "IITB_Academic_Block_Concrete_Log.xlsx"))
    print(f"Generated multi-sheet Excel file: {excel_path}")

    # 2. Generate Individual CSV Files
    csv_mat_path = os.path.join(sample_dir, "concrete_materials_sample.csv")
    pd.DataFrame(data["materials"]).to_csv(csv_mat_path, index=False)

    csv_tr_path = os.path.join(sample_dir, "concrete_transport_sample.csv")
    pd.DataFrame(data["transport"]).to_csv(csv_tr_path, index=False)

    csv_eq_path = os.path.join(sample_dir, "concrete_equipment_sample.csv")
    pd.DataFrame(data["equipment"]).to_csv(csv_eq_path, index=False)

    csv_stg_path = os.path.join(sample_dir, "concrete_stages_timeline.csv")
    pd.DataFrame(data["stages"]).to_csv(csv_stg_path, index=False)

    # 3. Verified Mahindra Eden Baseline Reference Files
    baseline_data = [
        {"emission_stage": "A1-A3 Product", "emissions_tco2e": 29066.46, "intensity_tco2e_per_m2": 297.11},
        {"emission_stage": "A4 Transport", "emissions_tco2e": 1705.57, "intensity_tco2e_per_m2": 17.43},
        {"emission_stage": "A5 Construction", "emissions_tco2e": 698.68, "intensity_tco2e_per_m2": 7.14},
        {"emission_stage": "Total", "emissions_tco2e": 31311.61, "intensity_tco2e_per_m2": 321.68}
    ]
    pd.DataFrame(baseline_data).to_csv(os.path.join(sample_dir, "mahindra_eden_carbon_baseline.csv"), index=False)

    ef_data = [
        {"material_name": "OPC Cement", "unit": "kg", "emission_factor": 0.996, "ef_source": "GKSPL Whole Life Carbon Study"},
        {"material_name": "M-Sand", "unit": "kg", "emission_factor": 0.0071, "ef_source": "GKSPL Whole Life Carbon Study"},
        {"material_name": "Coarse Aggregates", "unit": "kg", "emission_factor": 0.0058, "ef_source": "GKSPL Whole Life Carbon Study"},
        {"material_name": "Reinforcement Steel", "unit": "kg", "emission_factor": 2.397, "ef_source": "GKSPL Whole Life Carbon Study"},
        {"material_name": "Solid Concrete Block", "unit": "m3", "emission_factor": 188.450, "ef_source": "GKSPL Whole Life Carbon Study"},
        {"material_name": "M30 Concrete", "unit": "m3", "emission_factor": 273.683, "ef_source": "GKSPL Whole Life Carbon Study"}
    ]
    pd.DataFrame(ef_data).to_csv(os.path.join(sample_dir, "material_emission_factors.csv"), index=False)

    # 4. Generate Blank Template Excel Files
    template_path = os.path.join(template_dir, "Concrete_Twin_Template.xlsx")
    with pd.ExcelWriter(template_path, engine="openpyxl") as writer:
        pd.DataFrame([
            {"Property": "project_name", "Value": "Mahindra Eden - Whole Life Carbon Study"},
            {"Property": "contractor", "Value": "Mahindra Lifespaces / GKSPL"},
            {"Property": "location", "Value": "Bengaluru, Karnataka, India"},
            {"Property": "concrete_volume_m3", "Value": 55480.98},
            {"Property": "concrete_grade", "Value": "M30 Design Mix"},
            {"Property": "carbon_budget_tonnes", "Value": 31311.61},
            {"Property": "start_date", "Value": "2023-01-01"},
            {"Property": "target_completion_date", "Value": "2025-05-31"}
        ]).to_excel(writer, sheet_name="Project_Meta", index=False)

        pd.DataFrame(columns=[
            "material_name", "category", "unit", "planned_quantity",
            "delivered_quantity", "consumed_quantity", "waste_percentage",
            "waste_quantity", "emission_factor", "ef_source"
        ]).to_excel(writer, sheet_name="Materials", index=False)

        pd.DataFrame(columns=[
            "material_name", "vehicle_type", "quantity_transported",
            "unit", "distance_km", "round_trip", "transport_ef", "ef_source"
        ]).to_excel(writer, sheet_name="Transport", index=False)

        pd.DataFrame(columns=[
            "equipment_name", "category", "fuel_type", "hours_operated",
            "fuel_consumption_rate", "fuel_consumed", "emission_factor", "notes"
        ]).to_excel(writer, sheet_name="Equipment", index=False)

        pd.DataFrame(columns=[
            "stage_id", "name", "date", "volume_m3", "status", "description"
        ]).to_excel(writer, sheet_name="Stages", index=False)

    shutil.copy(template_path, os.path.join(template_dir, "IITB_Concrete_Twin_Template.xlsx"))
    print(f"Generated sample and template files successfully.")

if __name__ == "__main__":
    generate_sample_files()
