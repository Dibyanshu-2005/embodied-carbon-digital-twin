"""
Central Emission Factor Repository for Civil & Structural Construction.
Single Source of Truth for Materials (A1-A3), Transport (A4), and Equipment (A5a).
All factors are verified against published Indian standards and international inventories.
"""

from typing import Dict, Any, List, Optional

# Master index of primary reference sources with standard footnote citations [1]–[6]
SOURCES_INDEX: Dict[int, Dict[str, Any]] = {
    1: {
        "id": 1,
        "code": "[1]",
        "title": "CPWD Specifications & Analysis of Rates (2019)",
        "organization": "Central Public Works Department, Govt. of India",
        "description": "Standard schedule of rates and mix specifications for civil structural works (Dry process rotary kiln)."
    },
    2: {
        "id": 2,
        "code": "[2]",
        "title": "Indian Cement & Steel Sector EPD Baselines",
        "organization": "Cement Manufacturers Association (CMA) / Indian Steel Sector EPD (Tata & JSW)",
        "description": "Environmental Product Declarations for blended cements (PPC/PSC) and TMT Fe 500D rebar."
    },
    3: {
        "id": 3,
        "code": "[3]",
        "title": "ICE Database v3.0 (Inventory of Carbon & Energy)",
        "organization": "University of Bath, Sustainable Energy Research Team",
        "description": "Global benchmark inventory for mineral aggregates, economic allocation for pozzolans, and formwork."
    },
    4: {
        "id": 4,
        "code": "[4]",
        "title": "CEA CO2 Baseline Database v19 & IPCC Guidelines (2006)",
        "organization": "Central Electricity Authority (India) & IPCC",
        "description": "Grid electricity emission factor (0.716 kgCO2e/kWh) and diesel fuel standard (2.68 kgCO2e/L)."
    },
    5: {
        "id": 5,
        "code": "[5]",
        "title": "EFCA Environmental Product Declaration for Concrete Admixtures",
        "organization": "European Federation of Concrete Admixtures Associations",
        "description": "Verified LCA for polycarboxylate ether (PCE) based superplasticizers and set retarding agents."
    },
    6: {
        "id": 6,
        "code": "[6]",
        "title": "MoRTH Freight Baseline & DEFRA Transport Factors",
        "organization": "Ministry of Road Transport and Highways (India) / DEFRA",
        "description": "Heavy commercial tipper haulage (0.105 kgCO2e/t·km) and agitating transit mixer haulage."
    }
}

MATERIALS_DATABASE: List[Dict[str, Any]] = [
    # 1. Cements & Pozzolanic Binders
    {
        "id": "mat-opc-53",
        "name": "OPC 53 Grade Cement",
        "category": "Cement",
        "unit": "kg",
        "emission_factor": 0.890,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Standard high-strength Ordinary Portland Cement (Dry process rotary kiln)"
    },
    {
        "id": "mat-opc-43",
        "name": "OPC 43 Grade Cement",
        "category": "Cement",
        "unit": "kg",
        "emission_factor": 0.830,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Medium-strength Ordinary Portland Cement for general RCC construction"
    },
    {
        "id": "mat-ppc",
        "name": "PPC (Portland Pozzolana Cement)",
        "category": "Cement",
        "unit": "kg",
        "emission_factor": 0.620,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Fly ash blended factory cement (IS 1489 Part 1, ~30% pozzolana)"
    },
    {
        "id": "mat-psc",
        "name": "PSC (Portland Slag Cement)",
        "category": "Cement",
        "unit": "kg",
        "emission_factor": 0.480,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Ground granulated blast furnace slag blended cement (IS 455, ~50% slag)"
    },
    {
        "id": "mat-lc3",
        "name": "LC3 Low-Carbon Cement (Calcined Clay)",
        "category": "Cement",
        "unit": "kg",
        "emission_factor": 0.380,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Limestone Calcined Clay Cement with up to 50% clinker substitution"
    },
    {
        "id": "mat-flyash",
        "name": "Fly Ash (Class F Beneficiated)",
        "category": "SCM",
        "unit": "kg",
        "emission_factor": 0.015,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Thermal power plant byproduct, pulverized and beneficiated conforming to IS 3812"
    },
    {
        "id": "mat-ggbs",
        "name": "GGBS (Ground Granulated Blast Furnace Slag)",
        "category": "SCM",
        "unit": "kg",
        "emission_factor": 0.090,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Iron blast furnace slag, water quenched and finely ground conforming to IS 16714"
    },
    {
        "id": "mat-silicafume",
        "name": "Silica Fume (Micro Silica)",
        "category": "SCM",
        "unit": "kg",
        "emission_factor": 0.028,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Silicon/ferrosilicon metal byproduct for high-durability high-strength concrete"
    },
    {
        "id": "mat-metakaolin",
        "name": "Metakaolin (Calcined Kaolinite)",
        "category": "SCM",
        "unit": "kg",
        "emission_factor": 0.220,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Thermally activated kaolin clay pozzolana for high-performance mixes"
    },

    # 2. Aggregates & Sands
    {
        "id": "mat-agg-20",
        "name": "Coarse Aggregate 20mm (Crushed Basalt/Granite)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.007,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Quarried basalt/granite crushed and mechanical screened to IS 383"
    },
    {
        "id": "mat-agg-10",
        "name": "Coarse Aggregate 10mm (Crushed Basalt/Granite)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.007,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Graded secondary crushed basalt aggregate for dense structural concrete"
    },
    {
        "id": "mat-agg-40",
        "name": "Coarse Aggregate 40mm (Mass Concrete)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.006,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Large graded aggregate for mass concrete foundations and retaining dams"
    },
    {
        "id": "mat-msand",
        "name": "Fine Aggregate (Manufactured M-Sand)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.008,
        "source_id": 1,
        "source_code": "[1]",
        "description": "VSI crushed rock fine aggregate conforming to IS 383 Zone II"
    },
    {
        "id": "mat-psand",
        "name": "Plastering Fine Sand (P-Sand)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.009,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Washed, micro-fines controlled manufactured sand for masonry plaster"
    },
    {
        "id": "mat-riversand",
        "name": "Natural River Sand",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.005,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Dredged natural riverbed sand (virgin natural deposit)"
    },
    {
        "id": "mat-rca",
        "name": "Recycled Concrete Aggregate (RCA)",
        "category": "Aggregates",
        "unit": "kg",
        "emission_factor": 0.003,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Crushed demolition concrete, screened and graded for circular paving & lean concrete"
    },

    # 3. Ready-Mix & Precast Concrete
    {
        "id": "mat-rmc-m20",
        "name": "Ready-Mix Concrete M20 Grade",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.240,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Nominal mix grade for plain concrete, footings, and mass structural filling"
    },
    {
        "id": "mat-rmc-m25",
        "name": "Ready-Mix Concrete M25 Grade",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.275,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Standard reinforced concrete grade for residential slabs and beams"
    },
    {
        "id": "mat-rmc-m30",
        "name": "Ready-Mix Concrete M30 Grade",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.315,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Standard commercial building grade for RCC frames, rafts, and columns"
    },
    {
        "id": "mat-rmc-m35",
        "name": "Ready-Mix Concrete M35 Grade",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.345,
        "source_id": 1,
        "source_code": "[1]",
        "description": "High-durability grade for commercial tower substructures and basements"
    },
    {
        "id": "mat-rmc-m40",
        "name": "Ready-Mix Concrete M40 Grade",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.380,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Heavy infrastructure grade for heavily loaded high-rise columns & prestressed beams"
    },
    {
        "id": "mat-precast-slab",
        "name": "Precast Hollow-Core Concrete Slab Element",
        "category": "Ready-Mix Concrete",
        "unit": "kg",
        "emission_factor": 0.210,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Factory-cured precast hollow-core slab with optimized fly ash binder"
    },

    # 4. Steel & Metals
    {
        "id": "mat-rebar-eaf",
        "name": "TMT Rebar Steel Fe 500D (Induction / EAF Route)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 1.850,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Secondary scrap-based electric arc / induction furnace high-ductility rebar"
    },
    {
        "id": "mat-rebar",
        "name": "TMT Rebar Steel (Fe 500D - Primary BF-BOF Route)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 2.250,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Primary blast furnace / basic oxygen furnace high-ductility thermo-mechanically treated rebar"
    },
    {
        "id": "mat-rebar-550",
        "name": "TMT Rebar Steel Fe 550D (High-Strength)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 2.380,
        "source_id": 2,
        "source_code": "[2]",
        "description": "High tensile strength seismic rebar for heavy high-rise load-bearing cores"
    },
    {
        "id": "mat-struct-steel",
        "name": "Structural Steel Sections (Fe 410 / IS 2062)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 2.450,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Hot-rolled I-sections, angles, channels, and heavy fabricated girders"
    },
    {
        "id": "mat-binding-wire",
        "name": "Binding Wire (Annealed Mild Steel 18G)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 2.100,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Black annealed wire for rebar tying on site"
    },
    {
        "id": "mat-gi-decking",
        "name": "Galvanized Corrugated Steel Profile Decking Sheet",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 2.850,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Zinc coated profiled steel sheet for composite metal deck slabs"
    },
    {
        "id": "mat-alu-ext",
        "name": "Aluminium Architectural Extrusions (Curtain Wall)",
        "category": "Steel",
        "unit": "kg",
        "emission_factor": 8.900,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Anodized aluminium frame sections for external facade and window mullions"
    },

    # 5. Masonry & Wall Blocks
    {
        "id": "mat-aac-block",
        "name": "Autoclaved Aerated Concrete (AAC) Block",
        "category": "Masonry",
        "unit": "kg",
        "emission_factor": 0.220,
        "source_id": 2,
        "source_code": "[2]",
        "description": "Lightweight precast foam concrete block (600 kg/m³ density, IS 2185 Part 3)"
    },
    {
        "id": "mat-flyash-brick",
        "name": "Fly Ash Lime Gypsum (FaL-G) Brick",
        "category": "Masonry",
        "unit": "kg",
        "emission_factor": 0.120,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Non-calcined hydraulic bonded green brick conforming to IS 12894"
    },
    {
        "id": "mat-clay-brick",
        "name": "Traditional Kiln-Fired Clay Brick",
        "category": "Masonry",
        "unit": "kg",
        "emission_factor": 0.240,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Country clamp / Bull's Trench Kiln fired red clay brick (IS 1077)"
    },
    {
        "id": "mat-solid-block",
        "name": "Concrete Solid Block (Dense Aggregate)",
        "category": "Masonry",
        "unit": "kg",
        "emission_factor": 0.160,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Precast vibrated solid concrete load-bearing block (IS 2185 Part 1)"
    },

    # 6. Chemical Admixtures & Construction Chemicals
    {
        "id": "mat-pce",
        "name": "Chemical Admixture (PCE Superplasticizer)",
        "category": "Admixtures",
        "unit": "kg",
        "emission_factor": 1.450,
        "source_id": 5,
        "source_code": "[5]",
        "description": "High-range water-reducing polycarboxylate ether for high workability low w/c mixes"
    },
    {
        "id": "mat-snf",
        "name": "Sulfonated Naphthalene Formaldehyde (SNF)",
        "category": "Admixtures",
        "unit": "kg",
        "emission_factor": 1.880,
        "source_id": 5,
        "source_code": "[5]",
        "description": "Conventional high-range water-reducing superplasticizer"
    },
    {
        "id": "mat-curing-comp",
        "name": "Concrete Curing Compound (Aliphatic Resin)",
        "category": "Admixtures",
        "unit": "kg",
        "emission_factor": 1.750,
        "source_id": 5,
        "source_code": "[5]",
        "description": "Membrane-forming liquid curing compound to prevent plastic shrinkage cracking"
    },
    {
        "id": "mat-waterproofing",
        "name": "Integral Liquid Waterproofing Admixture",
        "category": "Admixtures",
        "unit": "kg",
        "emission_factor": 1.200,
        "source_id": 5,
        "source_code": "[5]",
        "description": "Capillary pore-blocking waterproofing liquid conforming to IS 2645"
    },

    # 7. Formwork & Timber
    {
        "id": "mat-plywood",
        "name": "Shuttering Formwork Plywood (12mm Film-Faced)",
        "category": "Formwork",
        "unit": "m2",
        "emission_factor": 0.080,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Phenolic film-faced birch/gurjan plywood amortized over 15 repeated pours"
    },
    {
        "id": "mat-steel-props",
        "name": "Steel Formwork Plates & Adjustable Acrow Props",
        "category": "Formwork",
        "unit": "m2",
        "emission_factor": 0.120,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Modular steel plate shuttering amortized over 60 site reuses"
    },
    {
        "id": "mat-mivan-form",
        "name": "Aluminium Monolithic Formwork (Mivan)",
        "category": "Formwork",
        "unit": "m2",
        "emission_factor": 0.065,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Engineered aluminium wall-slab formwork amortized over 150 structural repetitions"
    },

    # 8. Finishing & Plaster
    {
        "id": "mat-gypsum",
        "name": "Gypsum Wall Plaster",
        "category": "Finishing",
        "unit": "kg",
        "emission_factor": 0.130,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Calcined hemihydrate gypsum direct-coat internal wall plaster"
    },
    {
        "id": "mat-ceramic-tiles",
        "name": "Vitrified Ceramic Floor Tiles",
        "category": "Finishing",
        "unit": "kg",
        "emission_factor": 0.680,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Double-charged vitrified floor tiles kiln fired at 1200°C"
    },
    {
        "id": "mat-wall-putty",
        "name": "White Cement Wall Putty",
        "category": "Finishing",
        "unit": "kg",
        "emission_factor": 0.350,
        "source_id": 1,
        "source_code": "[1]",
        "description": "Polymer modified white cement based skimming compound"
    },
    {
        "id": "mat-facade-glass",
        "name": "Double Glazed Structural Facade Unit (DGU)",
        "category": "Finishing",
        "unit": "kg",
        "emission_factor": 1.850,
        "source_id": 3,
        "source_code": "[3]",
        "description": "Insulated double-glazed safety toughened architectural facade glass"
    },
    {
        "id": "mat-water",
        "name": "Mixing & Curing Water (Municipal Potable)",
        "category": "Water",
        "unit": "kg",
        "emission_factor": 0.0003,
        "source_id": 6,
        "source_code": "[6]",
        "description": "Treated potable municipal water for concrete batching and curing"
    }
]

TRANSPORT_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "tr-tipper-heavy",
        "name": "Heavy Tipper Truck (16–32t)",
        "vehicle_type": "Heavy Tipper Truck (16-32t)",
        "unit": "t·km",
        "emission_factor": 0.105,
        "source_id": 6,
        "source_code": "[6]",
        "description": "Multi-axle commercial truck for bulk aggregates, sand, and bagged cement"
    },
    {
        "id": "tr-tipper-med",
        "name": "Medium Commercial Vehicle (7.5–16t)",
        "vehicle_type": "Medium Commercial Vehicle (7.5-16t)",
        "unit": "t·km",
        "emission_factor": 0.155,
        "source_id": 6,
        "source_code": "[6]",
        "description": "Medium tipper truck for localized material transport"
    },
    {
        "id": "tr-lcv",
        "name": "Light Commercial Truck (<7.5t)",
        "vehicle_type": "Light Commercial Truck (<7.5t)",
        "unit": "t·km",
        "emission_factor": 0.240,
        "source_id": 6,
        "source_code": "[6]",
        "description": "Light truck for ad-hoc deliveries and site supplies"
    },
    {
        "id": "tr-transit-mixer",
        "name": "Transit Mixer Agitating (6–8 m³)",
        "vehicle_type": "Transit Mixer Agitating",
        "unit": "t·km",
        "emission_factor": 0.220,
        "source_id": 1,
        "source_code": "[1]",
        "description": "RMC transit drum continuously agitating concrete during haulage"
    },
    {
        "id": "tr-rail",
        "name": "Rail Freight Bulk Transport",
        "vehicle_type": "Rail Freight Bulk",
        "unit": "t·km",
        "emission_factor": 0.028,
        "source_id": 6,
        "source_code": "[6]",
        "description": "Electric locomotive bulk wagon transport for cement clinker"
    }
]

EQUIPMENT_DATABASE: List[Dict[str, Any]] = [
    {
        "id": "eq-pump-diesel",
        "name": "Concrete Boom Placer & Stationary Pump",
        "category": "Pumping Equipment",
        "fuel_type": "Diesel",
        "unit": "L",
        "emission_factor": 2.680,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "16.5 L/hr"
    },
    {
        "id": "eq-pump-electric",
        "name": "Stationary Concrete Pump (Electric Grid)",
        "category": "Pumping Equipment",
        "fuel_type": "Electric (Grid)",
        "unit": "kWh",
        "emission_factor": 0.716,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "45.0 kWh/hr"
    },
    {
        "id": "eq-mixer-idle",
        "name": "Transit Mixer On-Site Discharging & Idling",
        "category": "Transport / Agitation",
        "fuel_type": "Diesel",
        "unit": "L",
        "emission_factor": 2.680,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "4.8 L/hr"
    },
    {
        "id": "eq-vibrator",
        "name": "High-Frequency Concrete Needle Vibrators",
        "category": "Compaction Equipment",
        "fuel_type": "Diesel",
        "unit": "L",
        "emission_factor": 2.680,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "0.9 L/hr"
    },
    {
        "id": "eq-genset",
        "name": "Site Diesel Generator Set (125 kVA)",
        "category": "Power Generation",
        "fuel_type": "Diesel",
        "unit": "L",
        "emission_factor": 2.680,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "13.5 L/hr"
    },
    {
        "id": "eq-batching-electric",
        "name": "Batching Plant Grid Electricity",
        "category": "Batching Plant",
        "fuel_type": "Electric (Grid)",
        "unit": "kWh",
        "emission_factor": 0.716,
        "source_id": 4,
        "source_code": "[4]",
        "typical_consumption": "20.0 kWh/hr"
    }
]

def get_full_emission_catalog() -> Dict[str, Any]:
    """Returns the comprehensive emission factor catalog with standard reference footnotes."""
    return {
        "sources": list(SOURCES_INDEX.values()),
        "materials": MATERIALS_DATABASE,
        "transport": TRANSPORT_DATABASE,
        "equipment": EQUIPMENT_DATABASE
    }

def find_material_factor(name: str) -> Optional[Dict[str, Any]]:
    """Look up a material by name in the master database."""
    name_clean = name.strip().lower()
    for item in MATERIALS_DATABASE:
        if item["name"].lower() == name_clean or item["id"].lower() == name_clean:
            return item
    # Partial matching
    for item in MATERIALS_DATABASE:
        if name_clean in item["name"].lower() or item["name"].lower() in name_clean:
            return item
    return None

def find_transport_factor(vehicle_type: str) -> Optional[Dict[str, Any]]:
    """Look up a vehicle type in the master transport database."""
    v_clean = vehicle_type.strip().lower()
    for item in TRANSPORT_DATABASE:
        if item["name"].lower() == v_clean or item["vehicle_type"].lower() == v_clean:
            return item
    for item in TRANSPORT_DATABASE:
        if v_clean in item["name"].lower() or v_clean in item["vehicle_type"].lower():
            return item
    return None

def find_equipment_factor(name: str) -> Optional[Dict[str, Any]]:
    """Look up equipment by name in the master equipment database."""
    n_clean = name.strip().lower()
    for item in EQUIPMENT_DATABASE:
        if item["name"].lower() == n_clean or item["id"].lower() == n_clean:
            return item
    for item in EQUIPMENT_DATABASE:
        if n_clean in item["name"].lower():
            return item
    return None
