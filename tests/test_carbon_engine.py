"""
Unit tests for Concrete Construction Embodied Carbon Engine and Digital Twin.
Uses Python standard library unittest.
"""

import unittest
from engine.carbon_calculator import ConcreteCarbonEngine
from engine.digital_twin import ConcreteDigitalTwin
from engine.benchmarks import get_leti_band, evaluate_benchmarks, classify_concrete_mix
from engine.data_manager import DataManager
from sample_data.generate_samples import get_default_project_data

class TestCarbonEngine(unittest.TestCase):

    def test_mix_classification(self):
        self.assertIn("Green", classify_concrete_mix(220.0)["category"])
        self.assertIn("Blended", classify_concrete_mix(290.0)["category"])
        self.assertIn("Moderate", classify_concrete_mix(350.0)["category"])
        self.assertIn("High Carbon", classify_concrete_mix(400.0)["category"])

    def test_carbon_materials_calculation(self):
        materials = [
            {
                "material_name": "OPC 53 Cement",
                "category": "Cement",
                "consumed_quantity": 1000.0,
                "unit": "kg",
                "waste_percentage": 5.0,
                "emission_factor": 0.890
            },
            {
                "material_name": "Coarse Aggregate",
                "category": "Aggregates",
                "consumed_quantity": 2.0,
                "unit": "tonnes",  # 2000 kg
                "waste_percentage": 0.0,
                "emission_factor": 0.007
            }
        ]
        res = ConcreteCarbonEngine.calculate_materials_a1_a3(materials)
        # Cement: 1000 * 0.89 = 890 kgCO2e
        # Aggregate: 2000 * 0.007 = 14 kgCO2e
        # Total = 904 kgCO2e = 0.904 tCO2e
        self.assertAlmostEqual(res["total_emissions_kg"], 904.0, places=1)
        self.assertAlmostEqual(res["total_emissions_tonnes"], 0.904, places=3)
        # Waste penalty: 50 kg * 0.89 = 44.5 kgCO2e
        self.assertAlmostEqual(res["total_waste_penalty_kg"], 44.5, places=1)

    def test_transport_calculation(self):
        transport = [
            {
                "material_name": "Cement",
                "quantity_transported": 10.0, # 10 tonnes
                "distance_km": 100.0,
                "round_trip": False,
                "transport_ef": 0.105
            }
        ]
        res = ConcreteCarbonEngine.calculate_transport_a4(transport)
        # 10 tonnes * 100 km * 0.105 = 105 kgCO2e
        self.assertAlmostEqual(res["total_emissions_kg"], 105.0, places=1)
        self.assertAlmostEqual(res["total_tonne_km"], 1000.0, places=1)

    def test_equipment_calculation(self):
        equipment = [
            {
                "equipment_name": "Pump",
                "fuel_type": "Diesel",
                "fuel_consumed": 100.0, # 100 L
                "emission_factor": 2.68
            },
            {
                "equipment_name": "Mixer Electric",
                "fuel_type": "Electric",
                "fuel_consumed": 200.0, # 200 kWh
                "emission_factor": 0.716
            }
        ]
        res = ConcreteCarbonEngine.calculate_equipment_a5a(equipment)
        # Diesel: 100 * 2.68 = 268 kgCO2e
        # Electric: 200 * 0.716 = 143.2 kgCO2e
        # Total = 411.2 kgCO2e
        self.assertAlmostEqual(res["total_emissions_kg"], 411.2, places=1)

    def test_digital_twin_lifecycle_and_whatif(self):
        data = get_default_project_data()
        twin = ConcreteDigitalTwin(data)
        state = twin.get_full_state()

        self.assertGreater(state["summary"]["total_emissions_tonnes"], 0)
        self.assertGreater(state["summary"]["carbon_intensity_kg_per_m3"], 0)
        self.assertGreater(len(state["structural_twin"]["elements"]), 0)

        # Test What-If scenario (replace 40% cement with GGBS)
        sim = twin.simulate_what_if({
            "cement_replacement_pct": 40.0,
            "scm_type": "ggbs",
            "transport_distance_multiplier": 0.8,
            "waste_reduction_pct": 30.0
        })

        self.assertGreater(sim["carbon_saved_tonnes"], 0)
        self.assertGreater(sim["carbon_saved_pct"], 0)
        self.assertLess(sim["simulated_summary"]["total_emissions_tonnes"], state["summary"]["total_emissions_tonnes"])

    def test_excel_export_and_parse(self):
        data = get_default_project_data()
        twin = ConcreteDigitalTwin(data)
        excel_bytes = DataManager.export_project_to_excel(twin.get_full_state())
        self.assertGreater(len(excel_bytes), 0)

        parsed_state, msg = DataManager.parse_excel_bytes(excel_bytes)
        self.assertGreater(len(parsed_state["materials"]), 0)
        self.assertGreater(len(parsed_state["transport"]), 0)
        self.assertGreater(len(parsed_state["equipment"]), 0)

if __name__ == "__main__":
    unittest.main()
