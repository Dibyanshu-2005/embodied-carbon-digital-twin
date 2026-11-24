"""
Terminal CLI for Concrete Construction Embodied Carbon Monitoring.
Allows running carbon calculations, benchmark comparisons, and scenario evaluations directly from terminal.

Usage:
    python3 cli.py --demo
    python3 cli.py --file sample_data/IITB_Academic_Block_Concrete_Log.xlsx
    python3 cli.py --file sample_data/concrete_materials_sample.csv
"""

import sys
import argparse
from engine.digital_twin import ConcreteDigitalTwin
from engine.data_manager import DataManager
from sample_data.generate_samples import get_default_project_data

def print_banner():
    print("=" * 80)
    print("  DIGITAL TWIN: EMBODIED CARBON MONITORING SYSTEM (CONCRETE CONSTRUCTION)")
    print("  BTP Prototype - EN 15978 / ISO 21930 Standards Compliant")
    print("=" * 80)

def display_summary(twin: ConcreteDigitalTwin):
    state = twin.get_full_state()
    summary = state["summary"]
    benchmarks = state["benchmarks"]
    timeline = state["timeline"]

    print(f"\n[PROJECT OVERVIEW]")
    print(f"  Activity Name:      {summary['project_name']}")
    print(f"  Concrete Volume:    {summary['concrete_volume_m3']:.1f} m³ ({summary['concrete_grade']})")
    print(f"  Target Budget:      {summary['carbon_budget_tonnes']:.2f} tCO2e ({summary['target_budget_intensity_kg']:.1f} kgCO2e/m³)")
    print(f"  Construction Prog:  {timeline['overall_progress_pct']:.1f}% ({timeline['completed_volume_m3']:.1f} m³ completed)")

    print(f"\n[KEY CARBON METRICS]")
    print(f"  Total Upfront Carbon: {summary['total_emissions_tonnes']:.3f} tCO2e ({summary['total_emissions_kg']:,.1f} kgCO2e)")
    print(f"  Carbon Intensity:     {summary['carbon_intensity_kg_per_m3']:.1f} kgCO2e / m³")
    print(f"  Rebar Steel Ratio:    {summary['rebar_intensity_kg_per_m3']:.1f} kg steel / m³")
    print(f"  Wastage Carbon Loss:  {summary['waste_penalty_tonnes']:.3f} tCO2e ({summary['waste_penalty_pct']:.1f}% of total emissions)")

    print(f"\n[BENCHMARKING & RATING]")
    print(f"  Mix Category:         {benchmarks['mix_category']} ({benchmarks['mix_desc']})")
    print(f"  Budget Compliance:    {benchmarks['budget_status']}")
    print(f"  Vs CPWD Conventional: {benchmarks['savings_vs_conventional_pct']:.1f}% reduction")

    print(f"\n[LIFE CYCLE STAGES BREAKDOWN (EN 15978)]")
    print(f"  {'Module':<12} {'Description':<35} {'Emissions (t)':<15} {'Share (%)':<10}")
    print(f"  {'-'*12} {'-'*35} {'-'*15} {'-'*10}")
    for stage in summary["stage_breakdown"]:
        print(f"  {stage['module']:<12} {stage['label']:<35} {stage['emissions_tonnes']:<15.3f} {stage['share_pct']:<10.1f}")

    print(f"\n[TOP MATERIAL HOTSPOTS]")
    print(f"  {'Material Name':<35} {'Consumed Qty':<16} {'EF (kgCO2e/unit)':<18} {'Carbon (t)':<12} {'Share (%)'}")
    print(f"  {'-'*35} {'-'*16} {'-'*18} {'-'*12} {'-'*10}")
    for mat in summary["materials_module"]["items"][:6]:
        qty_str = f"{mat['consumed_quantity']:,.0f} {mat['unit']}"
        print(f"  {mat['material_name'][:33]:<35} {qty_str:<16} {mat['emission_factor']:<18.3f} {mat['carbon_emission_tonnes']:<12.3f} {mat['share_pct']:.1f}%")

    print("\n" + "=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Embodied Carbon CLI for Concrete Construction Digital Twin")
    parser.add_argument("--file", "-f", type=str, help="Path to Excel (.xlsx) or CSV file to calculate")
    parser.add_argument("--demo", action="store_true", help="Run with built-in demonstration activity data")
    parser.add_argument("--whatif", action="store_true", help="Simulate green substitution scenario (40% GGBS, 30% waste cut)")

    args = parser.parse_args()
    print_banner()

    if args.file:
        print(f"\n-> Loading dataset from: {args.file}")
        with open(args.file, "rb") as f:
            raw_bytes = f.read()
        parsed_data, msg = DataManager.parse_uploaded_file(args.file, raw_bytes)
        print(f"-> {msg}")
        twin = ConcreteDigitalTwin(parsed_data)
    else:
        print("\n-> Running with default demonstration dataset...")
        twin = ConcreteDigitalTwin()

    display_summary(twin)

    if args.whatif:
        print("\n[WHAT-IF SCENARIO: 40% GGBS SUBSTITUTION & 30% WASTE REDUCTION]")
        sim = twin.simulate_what_if({
            "cement_replacement_pct": 40.0,
            "scm_type": "ggbs",
            "transport_distance_multiplier": 0.8,
            "waste_reduction_pct": 30.0
        })
        print(f"  Original Emissions:   {twin.summary['total_emissions_tonnes']:.3f} tCO2e")
        print(f"  Optimized Emissions:  {sim['simulated_summary']['total_emissions_tonnes']:.3f} tCO2e")
        print(f"  Carbon Saved:         {sim['carbon_saved_tonnes']:.3f} tCO2e (-{sim['carbon_saved_pct']:.1f}%)")
        print(f"  New Carbon Intensity: {sim['simulated_summary']['carbon_intensity_kg_per_m3']:.1f} kgCO2e/m³")
        print(f"  New Mix Category:     {sim['simulated_benchmarks']['mix_category']}")
        print("=" * 80)

if __name__ == "__main__":
    main()
