"""
Sample Dataset Generator for Concrete Construction Embodied Carbon Monitoring.
Generates realistic civil engineering datasets for a concrete construction package:
- Multi-sheet Excel workbook (.xlsx)
- Individual CSV files for Materials, Transport, Equipment, and Stages
- Blank Excel template for user uploads
"""

import os
import pandas as pd
from typing import Dict, Any

def get_default_project_data() -> Dict[str, Any]:
    """Returns the default realistic concrete construction activity dataset."""
    project_meta = {
        "project_name": "Commercial Complex Construction Package",
        "contractor": "Civil & Structural Contractors",
        "location": "Project Site - Structural Zone A",
        "concrete_volume_m3": 420.0,
        "concrete_grade": "M30 Design Mix",
        "carbon_budget_tonnes": 115.0,
        "start_date": "2025-01-10",
        "target_completion_date": "2025-06-30"
    }

    materials = [
        {
            "material_name": "OPC 53 Grade Cement",
            "category": "Cement",
            "unit": "kg",
            "planned_quantity": 125000.0,
            "delivered_quantity": 134000.0,
            "consumed_quantity": 130000.0,
            "waste_percentage": 3.2,
            "waste_quantity": 4160.0,
            "emission_factor": 0.890,
            "ef_source": "Indian Cement EPD / CPWD Baseline (Dry Process Rotary Kiln)"
        },
        {
            "material_name": "Fly Ash (Class F Beneficiated)",
            "category": "SCM",
            "unit": "kg",
            "planned_quantity": 28000.0,
            "delivered_quantity": 30000.0,
            "consumed_quantity": 29000.0,
            "waste_percentage": 2.0,
            "waste_quantity": 580.0,
            "emission_factor": 0.015,
            "ef_source": "ICE Database v3.0 (Economic Allocation for Beneficiation & Transport)"
        },
        {
            "material_name": "Coarse Aggregate 20mm (Crushed Basalt)",
            "category": "Aggregates",
            "unit": "kg",
            "planned_quantity": 275000.0,
            "delivered_quantity": 290000.0,
            "consumed_quantity": 282000.0,
            "waste_percentage": 4.1,
            "waste_quantity": 11562.0,
            "emission_factor": 0.007,
            "ef_source": "ICE Database v3.0 (Crushed rock aggregate including quarrying)"
        },
        {
            "material_name": "Coarse Aggregate 10mm (Crushed Basalt)",
            "category": "Aggregates",
            "unit": "kg",
            "planned_quantity": 138000.0,
            "delivered_quantity": 145000.0,
            "consumed_quantity": 141000.0,
            "waste_percentage": 3.8,
            "waste_quantity": 5358.0,
            "emission_factor": 0.007,
            "ef_source": "ICE Database v3.0 (Crushed rock aggregate including quarrying)"
        },
        {
            "material_name": "Fine Aggregate (Manufactured M-Sand)",
            "category": "Aggregates",
            "unit": "kg",
            "planned_quantity": 235000.0,
            "delivered_quantity": 250000.0,
            "consumed_quantity": 242000.0,
            "waste_percentage": 4.5,
            "waste_quantity": 10890.0,
            "emission_factor": 0.008,
            "ef_source": "Indian LCI for VSI Crusher M-Sand"
        },
        {
            "material_name": "TMT Rebar Fe 500D (Primary Steel)",
            "category": "Reinforcement",
            "unit": "kg",
            "planned_quantity": 36000.0,
            "delivered_quantity": 40000.0,
            "consumed_quantity": 38500.0,
            "waste_percentage": 6.2,
            "waste_quantity": 2387.0,
            "emission_factor": 2.250,
            "ef_source": "Indian Steel Sector LCI (BF-BOF route EPD average)"
        },
        {
            "material_name": "Chemical Admixture (PCE Superplasticizer)",
            "category": "Admixtures",
            "unit": "kg",
            "planned_quantity": 2600.0,
            "delivered_quantity": 2800.0,
            "consumed_quantity": 2750.0,
            "waste_percentage": 1.5,
            "waste_quantity": 41.25,
            "emission_factor": 1.450,
            "ef_source": "EFCA Environmental Product Declaration"
        },
        {
            "material_name": "Mixing Water (Municipal Potable)",
            "category": "Water",
            "unit": "kg",
            "planned_quantity": 66000.0,
            "delivered_quantity": 66000.0,
            "consumed_quantity": 65000.0,
            "waste_percentage": 1.0,
            "waste_quantity": 650.0,
            "emission_factor": 0.0003,
            "ef_source": "UK DEFRA / Indian Municipal Pumping Baseline"
        },
        {
            "material_name": "Shuttering Formwork Plywood (12mm)",
            "category": "Formwork",
            "unit": "m2",
            "planned_quantity": 3200.0,
            "delivered_quantity": 3300.0,
            "consumed_quantity": 3250.0,
            "waste_percentage": 5.0,
            "waste_quantity": 162.5,
            "emission_factor": 0.080,
            "ef_source": "ICE Database v3.0 (Timber shuttering amortized over 15 pours)"
        }
    ]

    transport = [
        {
            "material_name": "Cement (OPC 53 Grade)",
            "vehicle_type": "Heavy Tipper Truck (16-32t)",
            "quantity_transported": 134.0,
            "unit": "tonnes",
            "distance_km": 175.0,
            "round_trip": False,
            "transport_ef": 0.105,
            "ef_source": "DEFRA / Indian Ministry of Road Transport freight factor"
        },
        {
            "material_name": "Fly Ash (Class F)",
            "vehicle_type": "Heavy Tipper Truck (16-32t)",
            "quantity_transported": 30.0,
            "unit": "tonnes",
            "distance_km": 95.0,
            "round_trip": False,
            "transport_ef": 0.105,
            "ef_source": "DEFRA / Indian Ministry of Road Transport freight factor"
        },
        {
            "material_name": "Crushed Basalt Aggregates (20mm + 10mm)",
            "vehicle_type": "Heavy Tipper Truck (16-32t)",
            "quantity_transported": 435.0,
            "unit": "tonnes",
            "distance_km": 42.0,
            "round_trip": False,
            "transport_ef": 0.105,
            "ef_source": "DEFRA / Indian Ministry of Road Transport freight factor"
        },
        {
            "material_name": "Manufactured M-Sand",
            "vehicle_type": "Heavy Tipper Truck (16-32t)",
            "quantity_transported": 250.0,
            "unit": "tonnes",
            "distance_km": 52.0,
            "round_trip": False,
            "transport_ef": 0.105,
            "ef_source": "DEFRA / Indian Ministry of Road Transport freight factor"
        },
        {
            "material_name": "TMT Rebar Fe 500D",
            "vehicle_type": "Heavy Tipper Truck (16-32t)",
            "quantity_transported": 40.0,
            "unit": "tonnes",
            "distance_km": 36.0,
            "round_trip": False,
            "transport_ef": 0.105,
            "ef_source": "DEFRA / Indian Ministry of Road Transport freight factor"
        },
        {
            "material_name": "Ready-Mix Wet Concrete (Transit Agitation)",
            "vehicle_type": "Ready-Mix Transit Mixer (Diesel)",
            "quantity_transported": 985.0,
            "unit": "tonnes",
            "distance_km": 14.0,
            "round_trip": True,
            "transport_ef": 0.220,
            "ef_source": "Indian RMCMA Transit Mixer Standard (Agitating Drum)"
        }
    ]

    equipment = [
        {
            "equipment_name": "Concrete Boom Placer & Stationary Pump",
            "category": "Pumping Equipment",
            "fuel_type": "Diesel",
            "hours_operated": 125.0,
            "fuel_consumption_rate": 16.5,
            "fuel_consumed": 2062.5,
            "emission_factor": 2.68,
            "notes": "Pumping M30 mix to foundation and elevated slabs"
        },
        {
            "equipment_name": "Transit Mixer On-Site Discharging & Idling",
            "category": "Transport / Agitation",
            "fuel_type": "Diesel",
            "hours_operated": 95.0,
            "fuel_consumption_rate": 4.8,
            "fuel_consumed": 456.0,
            "emission_factor": 2.68,
            "notes": "On-site turnaround and drum spinning"
        },
        {
            "equipment_name": "High-Frequency Concrete Needle Vibrators (x3)",
            "category": "Compaction Equipment",
            "fuel_type": "Diesel",
            "hours_operated": 140.0,
            "fuel_consumption_rate": 0.9,
            "fuel_consumed": 126.0,
            "emission_factor": 2.68,
            "notes": "Internal concrete compaction"
        },
        {
            "equipment_name": "Site Diesel Generator Set (125 kVA)",
            "category": "Power Generation",
            "fuel_type": "Diesel",
            "hours_operated": 150.0,
            "fuel_consumption_rate": 13.5,
            "fuel_consumed": 2025.0,
            "emission_factor": 2.68,
            "notes": "Site power for curing pumps, lights, and batch plant"
        },
        {
            "equipment_name": "Batching Plant Grid Electricity",
            "category": "Batching Plant",
            "fuel_type": "Electric (Grid)",
            "hours_operated": 110.0,
            "fuel_consumption_rate": 20.0,
            "fuel_consumed": 2200.0,
            "emission_factor": 0.716,
            "notes": "Pan mixer electric motor & aggregate conveyor"
        }
    ]

    stages = [
        {
            "stage_id": 1,
            "name": "Substructure Footings & Basement Raft",
            "date": "2025-01-20",
            "volume_m3": 110.0,
            "status": "Completed",
            "description": "Foundation concrete pour log and rebar delivery challans"
        },
        {
            "stage_id": 2,
            "name": "Plinth Beams & Ground Floor Columns",
            "date": "2025-02-15",
            "volume_m3": 75.0,
            "status": "Completed",
            "description": "Plinth tie beams and ground column casting log"
        },
        {
            "stage_id": 3,
            "name": "First Floor Slab & Retaining Wall",
            "date": "2025-03-25",
            "volume_m3": 95.0,
            "status": "Completed",
            "description": "First floor slab pouring and concrete delivery verification"
        },
        {
            "stage_id": 4,
            "name": "Second Floor Columns & Transfer Slab",
            "date": "2025-04-30",
            "volume_m3": 85.0,
            "status": "In Progress",
            "description": "Second floor columns and core structural elements"
        },
        {
            "stage_id": 5,
            "name": "Terrace Roof Slab & Overhead Tank",
            "date": "2025-06-15",
            "volume_m3": 55.0,
            "status": "Scheduled",
            "description": "Terrace roof slab casting and final structural milestone"
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
        # Meta sheet
        df_meta = pd.DataFrame([data["project_meta"]]).T.reset_index()
        df_meta.columns = ["Property", "Value"]
        df_meta.to_excel(writer, sheet_name="Project_Meta", index=False)

        # Materials sheet
        df_mat = pd.DataFrame(data["materials"])
        df_mat.to_excel(writer, sheet_name="Materials", index=False)

        # Transport sheet
        df_tr = pd.DataFrame(data["transport"])
        df_tr.to_excel(writer, sheet_name="Transport", index=False)

        # Equipment sheet
        df_eq = pd.DataFrame(data["equipment"])
        df_eq.to_excel(writer, sheet_name="Equipment", index=False)

        # Stages sheet
        df_stg = pd.DataFrame(data["stages"])
        df_stg.to_excel(writer, sheet_name="Stages", index=False)

    # Also keep copy for any legacy references
    import shutil
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

    print("Generated CSV sample files in sample_data/")

    # 3. Generate Blank User Template (.xlsx)
    template_excel_path = os.path.join(template_dir, "Concrete_Twin_Template.xlsx")
    with pd.ExcelWriter(template_excel_path, engine="openpyxl") as writer:
        # Meta template
        df_meta_tmpl = pd.DataFrame([
            {"Property": "project_name", "Value": "Your Project Name", "Instructions": "Name of construction activity / package"},
            {"Property": "concrete_volume_m3", "Value": 350.0, "Instructions": "Total design volume of concrete in cubic meters"},
            {"Property": "concrete_grade", "Value": "M30", "Instructions": "E.g., M25, M30, M35, M40"},
            {"Property": "carbon_budget_tonnes", "Value": 100.0, "Instructions": "Target embodied carbon ceiling in tonnes CO2e"},
            {"Property": "start_date", "Value": "2025-01-01", "Instructions": "YYYY-MM-DD"},
            {"Property": "target_completion_date", "Value": "2025-06-30", "Instructions": "YYYY-MM-DD"}
        ])
        df_meta_tmpl.to_excel(writer, sheet_name="Project_Meta", index=False)

        # Materials template with example row
        df_mat_tmpl = pd.DataFrame([
            {
                "material_name": "OPC 53 Grade Cement",
                "category": "Cement",
                "unit": "kg",
                "planned_quantity": 120000,
                "delivered_quantity": 125000,
                "consumed_quantity": 122000,
                "waste_percentage": 3.0,
                "waste_quantity": 3660,
                "emission_factor": 0.890,
                "ef_source": "Indian Cement EPD"
            },
            {
                "material_name": "Fine Aggregate (M-Sand)",
                "category": "Aggregates",
                "unit": "kg",
                "planned_quantity": 210000,
                "delivered_quantity": 220000,
                "consumed_quantity": 215000,
                "waste_percentage": 4.0,
                "waste_quantity": 8600,
                "emission_factor": 0.008,
                "ef_source": "ICE Database v3.0"
            }
        ])
        df_mat_tmpl.to_excel(writer, sheet_name="Materials", index=False)

        # Transport template
        df_tr_tmpl = pd.DataFrame([
            {
                "material_name": "Cement Deliveries",
                "vehicle_type": "Heavy Tipper Truck (16-32t)",
                "quantity_transported": 125.0,
                "unit": "tonnes",
                "distance_km": 150.0,
                "round_trip": False,
                "transport_ef": 0.105,
                "ef_source": "DEFRA freight standard"
            }
        ])
        df_tr_tmpl.to_excel(writer, sheet_name="Transport", index=False)

        # Equipment template
        df_eq_tmpl = pd.DataFrame([
            {
                "equipment_name": "Concrete Boom Pump",
                "category": "Pumping",
                "fuel_type": "Diesel",
                "hours_operated": 100.0,
                "fuel_consumption_rate": 15.0,
                "fuel_consumed": 1500.0,
                "emission_factor": 2.68,
                "notes": "Diesel pump"
            }
        ])
        df_eq_tmpl.to_excel(writer, sheet_name="Equipment", index=False)

        # Stages template
        df_stg_tmpl = pd.DataFrame([
            {
                "stage_id": 1,
                "name": "Foundations",
                "date": "2025-01-15",
                "volume_m3": 100.0,
                "status": "Completed",
                "description": "Footings"
            }
        ])
        df_stg_tmpl.to_excel(writer, sheet_name="Stages", index=False)

    shutil.copy(template_excel_path, os.path.join(template_dir, "IITB_Concrete_Twin_Template.xlsx"))
    print(f"Generated downloadable template: {template_excel_path}")

if __name__ == "__main__":
    generate_sample_files()
