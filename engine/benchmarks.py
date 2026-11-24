"""
Embodied Carbon Benchmarking Module for Concrete Construction.
References established published standards:
1. Indian CPWD (Central Public Works Department) Specifications 2019 / ICI Baseline
2. GRIHA (Green Rating for Integrated Habitat Assessment) Criterion 19 / IGBC Green Building Benchmark
3. ICE Database (Inventory of Carbon & Energy v3.0, University of Bath)
"""

from typing import Dict, Any, List

# Published Industry Reference Benchmarks (kgCO2e/m3 of concrete)
REFERENCE_BENCHMARKS = {
    "indian_cpwd_m30_baseline": {
        "name": "Conventional Indian M30 Baseline (100% OPC 53)",
        "intensity_kg_per_m3": 375.0,
        "source": "CPWD Specifications 2019 (Clause 5.1.2) / Indian Concrete Institute Baseline (380 kg OPC 53/m3)",
        "region": "India",
        "description": "Standard conventional M30 concrete in India using Ordinary Portland Cement without mineral admixtures."
    },
    "ice_v3_average_c30": {
        "name": "ICE Database v3.0 Typical Blended Concrete",
        "intensity_kg_per_m3": 298.0,
        "source": "Inventory of Carbon and Energy (ICE) v3.0, Craig Jones, University of Bath",
        "region": "Global Reference",
        "description": "Average cradle-to-gate intensity for ready-mix concrete with blended cementitious materials."
    },
    "indian_griha_green_target": {
        "name": "GRIHA / IGBC Green Building Target Mix",
        "intensity_kg_per_m3": 240.0,
        "source": "GRIHA v2019 Criterion 19 & Indian Ready Mixed Concrete Assoc (RMCMA)",
        "region": "India",
        "description": "Recommended green concrete practice in India achieving ~36% carbon reduction through SCM (Fly Ash / GGBS) substitution."
    },
    "mahindra_eden_gkspl": {
        "name": "Mahindra Eden Real Study (GKSPL)",
        "intensity_kg_per_m3": 273.68,
        "source": "GKSPL Whole Life Carbon Study / Mahindra Eden",
        "region": "India (Bengaluru)",
        "description": "Real-world observed baseline intensity for M30 ready mix concrete."
    }
}

# Concrete Mix Classification Categories
MIX_CATEGORIES = [
    {"category": "Green Concrete (GRIHA Target)", "max": 240.0, "color": "#10B981", "desc": "High SCM replacement (>40% Fly Ash or GGBS)"},
    {"category": "Blended Low-Carbon Mix", "max": 320.0, "color": "#059669", "desc": "Standard blended mix with Pozzolana / Fly Ash"},
    {"category": "Moderate Optimization Mix", "max": 375.0, "color": "#F59E0B", "desc": "Close to CPWD conventional baseline"},
    {"category": "High Carbon Mix (Above CPWD)", "max": 9999.0, "color": "#EF4444", "desc": "High-cement unoptimized pure OPC mix"}
]

def classify_concrete_mix(intensity_kg_per_m3: float) -> Dict[str, Any]:
    """Classify the concrete mix against standard thresholds."""
    for cat in MIX_CATEGORIES:
        if intensity_kg_per_m3 <= cat["max"]:
            return cat
    return MIX_CATEGORIES[-1]

# Retain helper for backward compatibility with tests
def get_leti_band(intensity_kg_per_m3: float) -> Dict[str, Any]:
    bands = [
        {"band": "A+", "min": 0, "max": 150, "color": "#10B981", "desc": "Ultra-Low Carbon"},
        {"band": "A", "min": 150, "max": 200, "color": "#059669", "desc": "Best Practice"},
        {"band": "B", "min": 200, "max": 250, "color": "#84CC16", "desc": "Good Practice"},
        {"band": "C", "min": 250, "max": 300, "color": "#EAB308", "desc": "Standard Blended Mix"},
        {"band": "D", "min": 300, "max": 350, "color": "#F97316", "desc": "Baseline"},
        {"band": "E", "min": 350, "max": 400, "color": "#EF4444", "desc": "High Cement OPC"},
        {"band": "F/G", "min": 400, "max": 9999, "color": "#991B1B", "desc": "Very High Carbon"}
    ]
    for b in bands:
        if b["min"] <= intensity_kg_per_m3 < b["max"]:
            return b
    return bands[-1]

def evaluate_benchmarks(actual_intensity_kg_per_m3: float, project_budget_kg_per_m3: float = 300.0) -> Dict[str, Any]:
    """
    Compare current concrete intensity against published benchmarks and project carbon budget.
    """
    mix_cat = classify_concrete_mix(actual_intensity_kg_per_m3)
    leti_rating = get_leti_band(actual_intensity_kg_per_m3)

    comparisons = []
    for key, bench in REFERENCE_BENCHMARKS.items():
        bench_val = bench["intensity_kg_per_m3"]
        diff_kg = actual_intensity_kg_per_m3 - bench_val
        diff_pct = (diff_kg / bench_val) * 100.0 if bench_val > 0 else 0.0

        comparisons.append({
            "key": key,
            "name": bench["name"],
            "benchmark_intensity": bench_val,
            "actual_intensity": actual_intensity_kg_per_m3,
            "difference_kg": round(diff_kg, 2),
            "difference_pct": round(diff_pct, 1),
            "status": "Lower Carbon" if diff_kg < 0 else "Higher Carbon",
            "source": bench["source"],
            "description": bench["description"]
        })

    # Project Budget Assessment
    budget_diff = actual_intensity_kg_per_m3 - project_budget_kg_per_m3
    budget_pct = (budget_diff / project_budget_kg_per_m3) * 100.0 if project_budget_kg_per_m3 > 0 else 0.0

    if budget_diff <= 0:
        budget_status = "Within Carbon Budget"
        budget_health = "good"
    elif budget_pct <= 10:
        budget_status = f"Slightly Over (+{budget_pct:.1f}%)"
        budget_health = "warning"
    else:
        budget_status = f"Over Budget (+{budget_pct:.1f}%)"
        budget_health = "danger"

    # Conventional Baseline Savings
    cpwd_baseline = REFERENCE_BENCHMARKS["indian_cpwd_m30_baseline"]["intensity_kg_per_m3"]
    savings_vs_conventional_pct = ((cpwd_baseline - actual_intensity_kg_per_m3) / cpwd_baseline) * 100.0

    return {
        "mix_category": mix_cat["category"],
        "mix_color": mix_cat["color"],
        "mix_desc": mix_cat["desc"],
        "leti_band": leti_rating["band"],
        "leti_color": leti_rating["color"],
        "leti_desc": leti_rating["desc"],
        "project_budget_kg_per_m3": project_budget_kg_per_m3,
        "budget_variance_kg": round(budget_diff, 2),
        "budget_variance_pct": round(budget_pct, 1),
        "budget_status": budget_status,
        "budget_health": budget_health,
        "savings_vs_conventional_pct": round(savings_vs_conventional_pct, 1),
        "benchmark_comparisons": comparisons
    }
