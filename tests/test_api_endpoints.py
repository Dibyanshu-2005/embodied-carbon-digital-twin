"""
API Integration Tests for FastAPI Carbon Digital Twin Server.
Uses Starlette TestClient.
"""

import os
import base64
import unittest
from starlette.testclient import TestClient
from app import app
from engine.data_manager import DataManager
from sample_data.generate_samples import get_default_project_data

class TestApiEndpoints(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_index_route(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Digital Twin: Embodied Carbon Monitoring", response.text)

    def test_get_project_api(self):
        response = self.client.get("/api/project")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("summary", data)
        self.assertIn("benchmarks", data)
        self.assertIn("structural_twin", data)
        self.assertGreater(data["summary"]["total_emissions_tonnes"], 0)

    def test_what_if_api(self):
        payload = {
            "cement_replacement_pct": 35.0,
            "scm_type": "fly_ash",
            "transport_distance_multiplier": 0.8,
            "waste_reduction_pct": 20.0,
            "electric_equipment": True
        }
        response = self.client.post("/api/what-if", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertGreater(data["result"]["carbon_saved_tonnes"], 0)

    def test_excel_export_api(self):
        response = self.client.get("/api/export/excel")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        self.assertGreater(len(response.content), 1000)

    def test_template_download_api(self):
        response = self.client.get("/api/templates/download")
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.content), 1000)

    def test_update_material_api(self):
        payload = {
            "index": 0,
            "updates": {"consumed_quantity": 140000.0},
            "reason": "Test edit"
        }
        response = self.client.post("/api/update/material", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        # Verify the new total updated
        mat0 = data["project_state"]["materials"][0]
        self.assertEqual(mat0["consumed_quantity"], 140000.0)

    def test_snapshot_api(self):
        payload = {
            "label": "Test Milestone 1",
            "author": "Tester"
        }
        response = self.client.post("/api/snapshot", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["snapshot"]["label"], "Test Milestone 1")

    def test_upload_excel_api(self):
        sample_path = "sample_data/IITB_Academic_Block_Concrete_Log.xlsx"
        self.assertTrue(os.path.exists(sample_path))
        with open(sample_path, "rb") as f:
            b64_content = base64.b64encode(f.read()).decode("utf-8")

        payload = {
            "filename": "IITB_Academic_Block_Concrete_Log.xlsx",
            "data": b64_content
        }
        response = self.client.post("/api/upload", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertIn("Materials", data["message"])
        self.assertGreater(data["project_state"]["summary"]["total_emissions_tonnes"], 0)

    def test_emission_factors_api(self):
        response = self.client.get("/api/emission-factors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("sources", data)
        self.assertIn("materials", data)
        self.assertIn("transport", data)
        self.assertIn("equipment", data)
        self.assertGreaterEqual(len(data["sources"]), 6)
        # Check source codes [1] to [6]
        codes = [s["code"] for s in data["sources"]]
        self.assertIn("[1]", codes)
        self.assertIn("[2]", codes)

    def test_add_continuous_periodic_stage_api(self):
        # Fetch current project state
        res_init = self.client.get("/api/project")
        init_data = res_init.json()
        last_stage = init_data["timeline"]["stages"][-1]
        last_date_str = last_stage["date"]
        import datetime
        last_date = datetime.date.fromisoformat(last_date_str)
        new_date = last_date + datetime.timedelta(days=30)

        payload = {
            "name": "Next Milestone: Site Completion",
            "date": new_date.isoformat(),
            "volume_m3": 45.0,
            "status": "Completed"
        }
        response = self.client.post("/api/stages/add", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["stage"]["duration_days"], 30)
        # Verify the timeline in project state updated continuously
        new_stages = data["project_state"]["timeline"]["stages"]
        added_stage = new_stages[-1]
        self.assertEqual(added_stage["stage_name"], "Next Milestone: Site Completion")
        self.assertEqual(added_stage["duration_days"], 30)

    def test_add_and_delete_material_api(self):
        # 1. Add Material from Central Repository
        payload = {
            "material_name": "Fly Ash (Class F Beneficiated)",
            "consumed_quantity": 15000.0,
            "waste_percentage": 2.5
        }
        res_add = self.client.post("/api/materials/add", json=payload)
        self.assertEqual(res_add.status_code, 200)
        data_add = res_add.json()
        self.assertTrue(data_add["success"])
        self.assertEqual(data_add["material"]["unit"], "kg")
        self.assertEqual(data_add["material"]["emission_factor"], 0.015)
        self.assertEqual(data_add["material"]["ef_source"], "[3]")

        # 2. Delete Material
        materials = data_add["project_state"]["materials"]
        idx_to_delete = len(materials) - 1
        res_del = self.client.post("/api/materials/delete", json={"index": idx_to_delete})
        self.assertEqual(res_del.status_code, 200)
        data_del = res_del.json()
        self.assertTrue(data_del["success"])
        self.assertEqual(len(data_del["project_state"]["materials"]), len(materials) - 1)

    def test_delete_transport_and_equipment_api(self):
        # Transport delete
        proj_res = self.client.get("/api/project")
        initial_tr_len = len(proj_res.json()["summary"]["transport_module"]["items"])
        res_del_tr = self.client.post("/api/transport/delete", json={"index": 0})
        self.assertEqual(res_del_tr.status_code, 200)
        self.assertEqual(len(res_del_tr.json()["project_state"]["transport"]), initial_tr_len - 1)

        # Equipment delete
        initial_eq_len = len(proj_res.json()["summary"]["equipment_module"]["items"])
        res_del_eq = self.client.post("/api/equipment/delete", json={"index": 0})
        self.assertEqual(res_del_eq.status_code, 200)
        self.assertEqual(len(res_del_eq.json()["project_state"]["equipment"]), initial_eq_len - 1)

    def test_delete_stage_api(self):
        proj_res = self.client.get("/api/project")
        stages = proj_res.json()["timeline"]["stages"]
        stage_to_del = stages[-1]["stage_id"]
        res_del_stg = self.client.post("/api/stages/delete", json={"stage_id": stage_to_del})
        self.assertEqual(res_del_stg.status_code, 200)
        data = res_del_stg.json()
        self.assertTrue(data["success"])
        self.assertEqual(len(data["project_state"]["timeline"]["stages"]), len(stages) - 1)

    def test_update_baseline_meta_api(self):
        payload = {
            "project_name": "Metro Viaduct Segment Package",
            "concrete_volume_m3": 550.0,
            "carbon_budget_tonnes": 140.0,
            "concrete_grade": "M35 High Performance Mix"
        }
        res = self.client.post("/api/update/meta", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        summary = data["project_state"]["summary"]
        self.assertEqual(summary["project_name"], "Metro Viaduct Segment Package")
        self.assertEqual(summary["concrete_volume_m3"], 550.0)
        self.assertEqual(summary["carbon_budget_tonnes"], 140.0)
        self.assertEqual(summary["concrete_grade"], "M35 High Performance Mix")

    def test_ocr_status_and_set_key_api(self):
        from engine.vision_ocr import get_groq_api_key, set_groq_api_key
        original_key = get_groq_api_key()
        try:
            # 1. Get status
            res = self.client.get("/api/ocr/status")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertIn("configured", data)
            self.assertIn("model", data)

            # 2. Set key validation
            res_empty = self.client.post("/api/ocr/set-key", json={"api_key": ""})
            self.assertEqual(res_empty.status_code, 400)

            # 3. Set valid key
            test_key = "gsk_test_mock_groq_key_12345"
            res_set = self.client.post("/api/ocr/set-key", json={"api_key": test_key})
            self.assertEqual(res_set.status_code, 200)
            self.assertTrue(res_set.json()["success"])

            # 4. Status reflects configured
            res_after = self.client.get("/api/ocr/status")
            self.assertEqual(res_after.status_code, 200)
            self.assertTrue(res_after.json()["configured"])
        finally:
            if original_key:
                set_groq_api_key(original_key)

    def test_ocr_add_verified_api(self):
        verified_items = [
            {
                "material_name": "OPC 53 Grade Cement",
                "category": "Cement",
                "unit": "kg",
                "consumed_quantity": 8000.0,
                "waste_percentage": 2.5,
                "emission_factor": 0.890,
                "ef_source": "[1]"
            },
            {
                "material_name": "Coarse Aggregate 20mm (Crushed Basalt/Granite)",
                "category": "Aggregates",
                "unit": "kg",
                "consumed_quantity": 18000.0,
                "waste_percentage": 3.5,
                "emission_factor": 0.007,
                "ef_source": "[3]"
            }
        ]

        init_res = self.client.get("/api/project")
        init_mats = len(init_res.json()["materials"])

        res = self.client.post("/api/ocr/add-verified", json={"materials": verified_items})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["added_count"], 2)
        self.assertEqual(len(data["project_state"]["materials"]), init_mats + 2)

    def test_ocr_parse_photos_missing_files(self):
        res = self.client.post("/api/ocr/parse-photos", json={"photos": []})
        self.assertEqual(res.status_code, 400)

    def test_update_stage_status_api(self):
        # Update stage 5 status from Scheduled to Completed
        res = self.client.post("/api/stages/update-status", json={"stage_id": 5, "status": "Completed"})
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        stg5 = [s for s in data["project_state"]["timeline"]["stages"] if s["stage_id"] == 5][0]
        self.assertEqual(stg5["status"], "Completed")
        self.assertGreater(stg5["stage_carbon_t"], 0.0)

        # Invalid status should return 400
        res_bad = self.client.post("/api/stages/update-status", json={"stage_id": 5, "status": "UnknownStatus"})
        self.assertEqual(res_bad.status_code, 400)

if __name__ == "__main__":
    unittest.main()
