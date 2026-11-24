# Digital Twin for Monitoring Embodied Carbon During Construction
### Bachelor of Technology Project (BTP) Prototype | Concrete Construction Package
**Compliant with EN 15978 / ISO 21930 Upfront Embodied Carbon Standards (Modules A1–A5)**

---

## 1. Project Overview

This prototype delivers a functional, dynamic **Digital Twin** system designed to monitor, track, and visualize the upfront embodied carbon generated during concrete construction activities in real time. 

Rather than treating embodied carbon as an static, post-construction calculation, this system maintains an evolving digital counterpart of the physical construction activity. As delivery notes, weighbridge tickets, batching records, and progress logs are uploaded or updated, the twin dynamically recalculates emissions, flags carbon hotspots, verifies budget compliance, and tracks progressive construction milestones without double-counting.

---

## 2. Theoretical & Mathematical Framework

### A. Lifecycle Scope (EN 15978 / ISO 21930 / RICS Framework)
The system calculates **Upfront Embodied Carbon (Cradle-to-Practical Completion)**:

$$\text{Total Upfront Carbon} = E_{A1-A3} + E_{A4} + E_{A5a} + E_{A5b}$$

1. **Module A1–A3: Product Stage (Raw Material Extraction, Processing & Manufacture)**
   $$E_{A1-A3} = \sum_{i} \Big( Q_{\text{consumed}, i} \times EF_{\text{mat}, i} \Big)$$
   - Primary drivers: Cement (OPC 53, OPC 43, PPC, PSC), Supplementary Cementitious Materials (Fly Ash, GGBS), Coarse Aggregates (10mm/20mm crushed stone), Fine Aggregates (River Sand vs Manufactured M-Sand), Mixing Water, Chemical Admixtures (PCE Superplasticizers), and TMT Steel Rebar (Fe 500D).

2. **Module A4: Transport to Construction Site**
   $$E_{A4} = \sum_{j} \Big( M_{\text{transported}, j} \times D_j \times EF_{\text{transport}, k} \Big)$$
   - Where $M_j$ is mass in tonnes, $D_j$ is effective haulage distance in km (with round-trip options for agitating transit mixers), and $EF_k$ is the vehicle mode emission factor ($\text{kgCO}_2\text{e}/\text{t}\cdot\text{km}$).

3. **Module A5a: Construction Installation (Site Plant & Equipment Energy)**
   $$E_{A5a} = \sum_{e} \Big( \text{Diesel Consumed}_e \times 2.68 + \text{Grid Electricity}_e \times 0.716 \Big)$$
   - Where $2.68\,\text{kgCO}_2\text{e}/\text{L}$ is the IPCC fuel emission standard and $0.716\,\text{kgCO}_2\text{e}/\text{kWh}$ is the Central Electricity Authority (CEA) Baseline Database for the Indian Power Grid.
   - Equipment tracked: Concrete Boom Placer & Stationary Pump, Transit Mixer On-Site Discharging & Idling, High-Frequency Needle Vibrators, Diesel Generator (DG Set), and Batching Plant Motors.

4. **Module A5b: Material Wastage & Scrap Accounting (Strict Non-Double Counting)**
   - In standard structural carbon accounting, delivered material $Q_{\text{delivered}} = Q_{\text{productive}} + Q_{\text{wasted}}$.
   - All consumed material is accounted for under $E_{A1-A3}$. The engine isolates and reports the **Wastage Carbon Penalty**:
     $$E_{\text{waste penalty}} = \sum_{i} \Big( Q_{\text{wasted}, i} \times EF_{\text{mat}, i} \Big)$$
   - Exposes hidden carbon losses from rebar off-cut scrap, concrete over-pour, and formwork degradation.

### B. Functional Units & Normalized Metrics
- **Concrete Mix Intensity**:
  $$I_{\text{mix}} = \frac{E_{\text{cementitious}} + E_{\text{aggregates}} + E_{\text{water}} + E_{\text{admixtures}}}{V_{\text{concrete}}} \quad [\text{kgCO}_2\text{e}/\text{m}^3]$$
- **Total Structural System Intensity**:
  $$I_{\text{struct}} = \frac{E_{\text{total}}}{V_{\text{concrete}}} \quad [\text{kgCO}_2\text{e}/\text{m}^3]$$
- **Rebar Reinforcement Ratio**:
  $$R_{\text{steel}} = \frac{M_{\text{rebar}}}{V_{\text{concrete}}} \quad [\text{kg steel}/\text{m}^3]$$

---

## 3. Benchmarking References

The application benchmarks project data against published standards:
1. **Conventional Indian M30 Baseline (CPWD Specifications 2019 / Clause 5.1.2)**:
   - Baseline intensity: $\approx 375\,\text{kgCO}_2\text{e}/\text{m}^3$ (Standard mix with 380 kg pure OPC 53 cement).
2. **GRIHA v2019 Criterion 19 / IGBC Green Building Target**:
   - Target intensity: $\le 240\,\text{kgCO}_2\text{e}/\text{m}^3$ ($\ge 25\text{--}36\%$ carbon reduction via Fly Ash / GGBS substitution).
3. **ICE Database v3.0 (Inventory of Carbon & Energy, University of Bath)**:
   - Typical global blended concrete average: $\approx 298\,\text{kgCO}_2\text{e}/\text{m}^3$.

---

## 4. Key Prototype Features

1. **Construction Activity Twin & Pour Progress Tracker**:
   - Tracks pour-by-pour concrete casting stages (Raft Foundations, Plinth Beams, Suspended Slabs, Columns).
   - Real-time pour telemetry: volume placed, mix design, cumulative carbon, and pour status.
2. **Strict Cumulative Historical S-Curve**:
   - Compares Planned Design S-Curve vs Actual Cumulative Logged Emissions vs Projected to Completion.
   - Ensures cumulative emissions strictly accumulate without fictitious drops.
3. **What-If Scenario Simulator & Sensitivity Analysis**:
   - Live sliders for SCM cement replacement (Fly Ash / GGBS), rebar scrap reduction, and equipment electrification.
   - Real-time before-and-after comparative cards with 1-click **"Commit Scenario to Digital Twin"** button.
4. **Flexible Excel (.xlsx) & CSV Ingestion**:
   - Multi-sheet and single-sheet auto-detection.
   - Resilient against column naming variations and missing optional fields.
   - In-app spreadsheet editor with live inline cell editing.
5. **Multi-Tab Excel Calculation Export**:
   - Generates formatted `.xlsx` reports containing Executive Summary, Material Breakdown, Transport Logs, Equipment Energy, and Version History.
6. **Immutable Audit Trail & Version Snapshots**:
   - Captures timestamped state snapshots with diff tracking.

---

## 5. Quick Start Instructions

### Prerequisites
- Python 3.10+
- Modern web browser (Chrome, Edge, Safari, Firefox)

### Running the Web Dashboard
```bash
# 1. Navigate to project root
cd /Users/rajat74/Desktop/C-Project/BTP

# 2. Run the start script
./run.sh

# Or directly with uvicorn:
PYTHONPATH=. python3 -m uvicorn app:app --port 8000 --reload
```
Open your browser to: **`http://localhost:8000`**

### Running the Terminal CLI
To calculate emissions or run what-if scenarios directly from the command line:
```bash
# Run with default demonstration dataset
PYTHONPATH=. python3 cli.py --demo

# Run with what-if green substitution scenario
PYTHONPATH=. python3 cli.py --demo --whatif

# Run with an external Excel file
PYTHONPATH=. python3 cli.py --file sample_data/IITB_Academic_Block_Concrete_Log.xlsx
```

### Running Automated Test Suite
```bash
PYTHONPATH=. python3 -m unittest discover tests -v
```

---

## 6. Professor Meeting Demonstration Guide

Follow these steps during your evaluation meeting to showcase the complete workflow:

| Step | Action | What to Explain to the Professor |
|---|---|---|
| **1. Overview & PM Focus** | Open `http://localhost:8000` | Explain the core problem: Traditional carbon accounting happens months after construction finishes when it is too late to act. This tool enables **periodic tracking (weekly DPRs / monthly delivery logs)** to control both carbon burn and material waste in real time. |
| **2. Key PM Metrics** | Review top KPI strip | Highlight the 4 critical metrics: Total Carbon vs Budget Ceiling, Site Wastage & Scrap Penalty ($10.8\,\text{tCO}_2\text{e}$ lost), Mix Carbon Intensity ($-20.5\%$ vs CPWD 2019 baseline), and Physical Progress. |
| **3. Project S-Curve & Burn Rate** | Inspect left chart on Dashboard | Walk through the non-decreasing S-Curve: Planned Baseline vs Actual Logged vs Projected to Completion. Click on any reporting period pill (e.g., `Month 1 Log` or `Month 2 Log`) to inspect telemetry. |
| **4. Carbon Drivers & BOQ Variance** | Toggle sub-buttons on right card | Click `Pareto Hotspots` to demonstrate that Cement & Steel account for ~89% of site footprint. Click `Planned vs Actual` to show where site material consumption deviated from the design BOQ. |
| **5. Decarbonization Planner (What-If)** | Adjust sliders directly on Dashboard | Adjust SCM Cement Replacement to 45% (GGBS) and Wastage Reduction to -50%. Show the instant reduction in total footprint ($-52.8\,\text{tCO}_2\text{e}$) and click **"Commit Scenario"** to update the twin version. |
| **6. Site Ingestion & Periodic Logs** | Switch to **"Site Ingestion & Periodic Logs"** tab | Demonstrate how a supervisor logs weekly deliveries. Double-click any cell in the Materials table to update quantities or scrap %; show the auto-calculation and audit snapshot trail. |
| **7. Official Standards & Export** | Click **"Export Excel (.xlsx)"** | Download the audit report containing multi-sheet calculations, and expand the CPWD 2019 / GRIHA 240 kg/m³ reference section to confirm documented emission factor sources. |

---

## 7. Repository Structure

```
BTP/
├── app.py                      # FastAPI server with REST APIs and template rendering
├── cli.py                      # Terminal CLI tool for carbon accounting
├── run.sh                      # One-click start shell script
├── README.md                   # Comprehensive engineering documentation & professor guide
├── engine/
│   ├── __init__.py
│   ├── carbon_calculator.py    # EN 15978 Modules A1-A5 calculation engine
│   ├── digital_twin.py         # State machine, stage logs, snapshots, 3D geometry generator
│   ├── benchmarks.py           # CPWD, GRIHA & ICE database benchmark engine
│   └── data_manager.py         # Excel (.xlsx) & CSV parser, validator, and report generator
├── sample_data/
│   ├── generate_samples.py     # Script generating realistic civil engineering datasets
│   ├── IITB_Academic_Block_Concrete_Log.xlsx # Multi-sheet Excel workbook (Meta, Materials, Transport, Equipment, Stages)
│   ├── concrete_materials_sample.csv
│   ├── concrete_transport_sample.csv
│   ├── concrete_equipment_sample.csv
│   └── concrete_stages_timeline.csv
├── static/
│   ├── css/
│   │   └── style.css           # Clean civil engineering dashboard stylesheet
│   ├── js/
│   │   ├── app.js              # State manager, event listeners, live edit handlers
│   │   ├── dashboard_charts.js # Interactive Chart.js visualizer (S-curve, Hotspots, Variance)
│   │   └── twin_3d.js          # Interactive 3D/Isometric Structural Twin Canvas visualizer
│   └── templates/
│       └── IITB_Concrete_Twin_Template.xlsx # Downloadable blank template for user datasets
├── templates/
│   └── index.html              # Modern single-page web dashboard
└── tests/
    ├── __init__.py
    ├── test_carbon_engine.py   # Unit tests for calculation formulas and edge cases
    └── test_api_endpoints.py   # Integration tests for REST APIs and file upload
```

---

## 8. Extensibility to Future Phases
This architecture was specifically structured to enable seamless extensions:
- **BIM Model Integration (IFC / Revit)**: Structural element geometry in `engine/digital_twin.py` can be populated directly from parsed IFC models.
- **OCR Invoicing**: Upload pipeline can feed supplier delivery challans into an OCR parser to auto-populate materials and transport haulage.
- **IoT Sensors**: Batching plant electricity meters and concrete maturity temperature sensors can stream real-time telemetry into `/api/update/...`.
- **Expansion to Other Activities**: The calculation modules (A1-A3, A4, A5) are decoupled and ready for Earthwork / Excavation, Masonry, Steel Superstructures, and Facades.
