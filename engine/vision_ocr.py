"""
Vision OCR Ingestion Module for Construction Site Delivery Challans & Invoices.
Uses Groq Multimodal Vision (Llama 3.2 Vision) to extract verified civil material line-items.
Enforces strict conservative extraction: ambiguous or illegible data is strictly omitted.
Matches all extracted items to the Central Emission Factor Repository (MATERIALS_DATABASE).
Generates ready-to-use partial CSV templates and enables 1-click active log synchronization.
"""

import os
import re
import json
import base64
import csv
import io
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from dotenv import load_dotenv

from engine.emission_database import MATERIALS_DATABASE, find_material_factor

# Load environment variables from .env if present
load_dotenv()

# In-memory runtime API key holder
_RUNTIME_GROQ_KEY: Optional[str] = None

# Active multimodal vision model on Groq
DEFAULT_VISION_MODEL = "qwen/qwen3.8-27b"
FALLBACK_VISION_MODEL = "qwen/qwen3.8-27b"

# Alias mapping dictionary for high-accuracy civil material resolution
MATERIAL_ALIASES = [
    # Cements
    (re.compile(r'\bopc\s*53\b', re.I), "mat-opc-53"),
    (re.compile(r'\bopc\s*43\b', re.I), "mat-opc-43"),
    (re.compile(r'\b(ppc|pozzolana|fly\s*ash\s*cement)\b', re.I), "mat-ppc"),
    (re.compile(r'\b(psc|slag\s*cement)\b', re.I), "mat-psc"),
    (re.compile(r'\b(lc3|calcined\s*clay)\b', re.I), "mat-lc3"),
    
    # SCMs
    (re.compile(r'\bfly\s*ash\b', re.I), "mat-flyash"),
    (re.compile(r'\b(ggbs|granulated\s*blast\s*furnace\s*slag)\b', re.I), "mat-ggbs"),
    (re.compile(r'\b(silica\s*fume|micro\s*silica)\b', re.I), "mat-silicafume"),
    (re.compile(r'\bmetakaolin\b', re.I), "mat-metakaolin"),
    
    # Aggregates & Sands
    (re.compile(r'\b(20\s*mm|ca\s*20|coarse\s*aggregate\s*20)\b', re.I), "mat-agg-20"),
    (re.compile(r'\b(10\s*mm|ca\s*10|coarse\s*aggregate\s*10)\b', re.I), "mat-agg-10"),
    (re.compile(r'\b(40\s*mm|ca\s*40|coarse\s*aggregate\s*40)\b', re.I), "mat-agg-40"),
    (re.compile(r'\b(m-?sand|manufactured\s*sand|crushed\s*sand|vsi\s*sand)\b', re.I), "mat-msand"),
    (re.compile(r'\b(p-?sand|plastering\s*sand)\b', re.I), "mat-psand"),
    (re.compile(r'\b(river\s*sand|natural\s*sand)\b', re.I), "mat-riversand"),
    (re.compile(r'\b(rca|recycled\s*aggregate)\b', re.I), "mat-rca"),
    
    # Ready Mix Concrete
    (re.compile(r'\b(m-?20|rmc\s*m-?20)\b', re.I), "mat-rmc-m20"),
    (re.compile(r'\b(m-?25|rmc\s*m-?25)\b', re.I), "mat-rmc-m25"),
    (re.compile(r'\b(m-?30|rmc\s*m-?30)\b', re.I), "mat-rmc-m30"),
    (re.compile(r'\b(m-?35|rmc\s*m-?35)\b', re.I), "mat-rmc-m35"),
    (re.compile(r'\b(m-?40|rmc\s*m-?40)\b', re.I), "mat-rmc-m40"),
    
    # Reinforcement Steel
    (re.compile(r'\b(fe\s*550d?|tmt\s*550d?)\b', re.I), "mat-rebar-550"),
    (re.compile(r'\b(fe\s*500d?|tmt\s*500d?|tmt\s*rebar|reinforcement\s*steel|steel\s*bar|rebar)\b', re.I), "mat-rebar"),
    (re.compile(r'\bbinding\s*wire\b', re.I), "mat-binding-wire"),
    
    # Admixtures
    (re.compile(r'\b(pce|superplasticizer|polycarboxylate)\b', re.I), "mat-pce"),
    (re.compile(r'\b(retarder|set\s*retarding)\b', re.I), "mat-snf"),
    (re.compile(r'\b(waterproofing|waterproof)\b', re.I), "mat-waterproofing"),
    
    # Water & Formwork
    (re.compile(r'\b(water|tanker\s*water|borewell)\b', re.I), "mat-water"),
    (re.compile(r'\b(plywood|shuttering\s*ply)\b', re.I), "mat-plywood")
]

DEFAULT_WASTE_PERCENTAGES = {
    "Cement": 2.5,
    "SCM": 2.0,
    "Aggregates": 3.5,
    "Steel": 4.0,
    "Ready-Mix Concrete": 2.0,
    "Admixtures": 1.0,
    "Water": 5.0,
    "Formwork": 1.0
}


def get_groq_api_key() -> Optional[str]:
    """Retrieve Groq API key from runtime memory, .env, or os environment."""
    global _RUNTIME_GROQ_KEY
    if _RUNTIME_GROQ_KEY:
        return _RUNTIME_GROQ_KEY.strip()
    env_key = os.environ.get("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    # Check .env file directly if exists
    env_file = Path(".env")
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    if line.startswith("GROQ_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            return val
        except Exception:
            pass
    return None


def set_groq_api_key(key: str) -> None:
    """Save Groq API key to runtime memory and persist to local .env."""
    global _RUNTIME_GROQ_KEY
    cleaned = key.strip()
    _RUNTIME_GROQ_KEY = cleaned
    os.environ["GROQ_API_KEY"] = cleaned

    env_path = Path(".env")
    lines = []
    found = False
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()
        new_lines = []
        for line in lines:
            if line.startswith("GROQ_API_KEY="):
                new_lines.append(f"GROQ_API_KEY={cleaned}\n")
                found = True
            else:
                new_lines.append(line)
        if not found:
            new_lines.append(f"GROQ_API_KEY={cleaned}\n")
        lines = new_lines
    else:
        lines = [f"GROQ_API_KEY={cleaned}\n"]

    with open(env_path, "w") as f:
        f.writelines(lines)


def is_groq_configured() -> bool:
    """Check if a non-empty Groq API key is currently configured."""
    key = get_groq_api_key()
    return bool(key and len(key) > 5)


def resolve_material_from_catalog(extracted_name: str, extracted_category: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Match an OCR-extracted material string against the master MATERIALS_DATABASE.
    Uses regex aliases followed by exact and partial database matching.
    """
    clean_name = extracted_name.strip()
    
    # 1. Alias regex matching
    for pattern, target_id in MATERIAL_ALIASES:
        if pattern.search(clean_name):
            for item in MATERIALS_DATABASE:
                if item["id"] == target_id:
                    return item

    # 2. Direct catalog helper search
    direct_match = find_material_factor(clean_name)
    if direct_match:
        return direct_match

    # 3. Category scoped match if category provided
    if extracted_category:
        cat_lower = extracted_category.strip().lower()
        for item in MATERIALS_DATABASE:
            if item["category"].lower() == cat_lower and (item["name"].lower() in clean_name.lower() or clean_name.lower() in item["name"].lower()):
                return item

    return None


def generate_partial_csv(materials: List[Dict[str, Any]]) -> str:
    """
    Generate standard partial materials CSV format from extracted items.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "material_name",
        "category",
        "unit",
        "consumed_quantity",
        "waste_percentage",
        "emission_factor",
        "ef_source"
    ])
    for m in materials:
        writer.writerow([
            m.get("material_name", ""),
            m.get("category", ""),
            m.get("unit", "kg"),
            m.get("consumed_quantity", 0.0),
            m.get("waste_percentage", 2.0),
            m.get("emission_factor", 0.0),
            m.get("ef_source", "[1]")
        ])
    return output.getvalue()


def call_groq_vision(image_base64: str, mime_type: str = "image/jpeg", api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Invoke Groq's multimodal Llama-3.2 Vision model to extract delivery challan data.
    Enforces conservative extraction: skips ambiguous or illegible lines.
    """
    import httpx

    key = api_key or get_groq_api_key()
    if not key:
        raise ValueError("Groq API key not configured. Please provide your GROQ_API_KEY.")

    system_prompt = (
        "You are an expert civil construction audit assistant specializing in materials OCR extraction from "
        "site delivery tickets, weighbridge slips, supplier delivery challans, and concrete batch invoices.\n\n"
        "RECOGNIZED CIVIL MATERIALS:\n"
        "- Cements: OPC 53, OPC 43, PPC, PSC, LC3\n"
        "- Pozzolans/SCM: Fly Ash, GGBS, Silica Fume, Metakaolin\n"
        "- Aggregates: Coarse Aggregate 20mm, 10mm, 40mm; Manufactured M-Sand, P-Sand, River Sand, Recycled Concrete Aggregate (RCA)\n"
        "- Ready-Mix Concrete: Grades M20, M25, M30, M35, M40, M50\n"
        "- Steel Rebar: TMT Fe 500D, Fe 550D, Binding Wire\n"
        "- Admixtures: PCE Superplasticizer, Retarder, Liquid Waterproofing\n"
        "- Water, Formwork Plywood\n\n"
        "STRICT CONSERVATIVE EXTRACTION RULES:\n"
        "1. Extract ONLY unambiguous, verified material delivery line items with clear quantities and units.\n"
        "2. If an item or number is blurry, illegible, partially cropped, or ambiguous, DO NOT guess or infer. Put it in 'ambiguous_or_skipped' with a short reason and NEVER add it to extracted_items.\n"
        "3. IGNORE non-material entries (e.g. freight haulage cost, tax/GST lines, vehicle license plate numbers, weighbridge tare weight, driver allowance).\n"
        "4. Standardize units: 'kg', 'tonnes', 'm3', 'L', 'bags'. (Note: 1 cement bag = 50 kg).\n"
        "5. Output valid JSON ONLY matching the required schema."
    )

    user_prompt = (
        "Analyze this construction delivery challan / ticket image.\n"
        "Extract confirmed material records and skip all ambiguous or non-material lines.\n\n"
        "Required JSON schema:\n"
        "{\n"
        '  "document_type": "Delivery Challan / Weighbridge Slip / Invoice / Unknown",\n'
        '  "vendor": "Supplier or Vendor Name or null",\n'
        '  "ticket_number": "Challan or Ticket # or null",\n'
        '  "date": "YYYY-MM-DD or null",\n'
        '  "extracted_items": [\n'
        '    {\n'
        '      "raw_text": "Original line text from challan",\n'
        '      "material_name": "Standardized material name",\n'
        '      "category": "Cement | Aggregates | SCM | Steel | Ready-Mix Concrete | Admixtures | Water | Formwork",\n'
        '      "quantity": 10000.0,\n'
        '      "unit": "kg | tonnes | m3 | L | bags",\n'
        '      "confidence": 0.95\n'
        '    }\n'
        '  ],\n'
        '  "ambiguous_or_skipped": [\n'
        '    {\n'
        '      "raw_text": "Uncertain text or illegible row",\n'
        '      "reason": "Quantity illegible or unrecognized material grade"\n'
        '    }\n'
        '  ]\n'
        "}"
    )

    image_data_url = f"data:{mime_type};base64,{image_base64}"

    payload = {
        "model": DEFAULT_VISION_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": user_prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url}
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 1200,
        "response_format": {"type": "json_object"}
    }

    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }

    url = "https://api.groq.com/openai/v1/chat/completions"

    with httpx.Client(timeout=45.0) as client:
        response = client.post(url, headers=headers, json=payload)
        
        # If rate-limited or preview model issue, try fallback model
        if response.status_code == 400 and DEFAULT_VISION_MODEL in response.text:
            payload["model"] = FALLBACK_VISION_MODEL
            response = client.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            raise RuntimeError(f"Groq API error ({response.status_code}): {response.text}")

        res_data = response.json()
        content = res_data["choices"][0]["message"]["content"]
        
        # Parse JSON output safely
        try:
            return json.loads(content)
        except Exception:
            # Fallback substring extraction
            start = content.find("{")
            end = content.rfind("}")
            if start != -1 and end != -1:
                return json.loads(content[start:end+1])
            raise ValueError(f"Failed to parse LLM vision output: {content}")


def process_challan_photos(
    photos_data: List[Tuple[str, bytes, str]], 
    api_key: Optional[str] = None,
    mock_items: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Process one or more uploaded delivery challan photos:
    1. Runs Groq Vision OCR extraction (or mock if requested).
    2. Filters out ambiguous data.
    3. Normalizes units (e.g. bags -> kg, tonnes -> kg).
    4. Matches items to master emission library.
    5. Computes embodied carbon and generates a partial CSV template.
    """
    verified_materials: List[Dict[str, Any]] = []
    omitted_items: List[Dict[str, Any]] = []
    documents_summary: List[Dict[str, Any]] = []

    # Mock mode support (useful for offline unit testing without live API keys)
    if mock_items is not None:
        raw_extractions = [{
            "document_type": "Delivery Challan (Mock)",
            "vendor": "UltraTech RMC / JSW Steel",
            "date": "2025-02-15",
            "extracted_items": mock_items,
            "ambiguous_or_skipped": [
                {"raw_text": "Scribbled misc charges - 500", "reason": "Non-material freight charge; skipped for carbon audit."}
            ]
        }]
    else:
        raw_extractions = []
        for filename, photo_bytes, mime_type in photos_data:
            b64_str = base64.b64encode(photo_bytes).decode("utf-8")
            doc_result = call_groq_vision(b64_str, mime_type=mime_type, api_key=api_key)
            doc_result["filename"] = filename
            raw_extractions.append(doc_result)

    # Process extracted items across all documents
    for doc in raw_extractions:
        doc_info = {
            "filename": doc.get("filename", "challan_photo"),
            "document_type": doc.get("document_type", "Challan"),
            "vendor": doc.get("vendor"),
            "ticket_number": doc.get("ticket_number"),
            "date": doc.get("date")
        }
        documents_summary.append(doc_info)

        # 1. Process verified items
        for item in doc.get("extracted_items", []):
            raw_name = item.get("material_name", "")
            raw_category = item.get("category", "")
            qty = float(item.get("quantity", 0.0) or 0.0)
            unit = str(item.get("unit", "kg")).strip().lower()

            if qty <= 0:
                omitted_items.append({
                    "raw_text": f"{raw_name} (Zero or missing quantity)",
                    "reason": "Zero or non-positive quantity specified on challan."
                })
                continue

            # Standardize unit conversion
            # Cement bags to kg (1 bag = 50 kg)
            if unit in ["bag", "bags", "pkt", "pkts", "sack", "sacks"]:
                qty = qty * 50.0
                unit = "kg"
            elif unit in ["tonne", "tonnes", "t", "mt", "metric tonne", "ton"]:
                qty = qty * 1000.0
                unit = "kg"

            # Match against central emission database
            matched = resolve_material_from_catalog(raw_name, raw_category)

            if matched:
                category = matched["category"]
                standard_name = matched["name"]
                emission_factor = float(matched["emission_factor"])
                ef_source = matched.get("source_code", "[1]")
                waste_pct = DEFAULT_WASTE_PERCENTAGES.get(category, 2.5)

                # Calculate embodied carbon
                # Carbon (tCO2e) = (qty * emission_factor * (1 + waste_pct/100)) / 1000.0
                carbon_tco2e = round((qty * emission_factor * (1.0 + (waste_pct / 100.0))) / 1000.0, 4)

                verified_materials.append({
                    "material_name": standard_name,
                    "category": category,
                    "unit": unit,
                    "consumed_quantity": round(qty, 2),
                    "planned_quantity": round(qty, 2),
                    "waste_percentage": waste_pct,
                    "emission_factor": emission_factor,
                    "ef_source": ef_source,
                    "carbon_tonnes": carbon_tco2e,
                    "raw_extracted": raw_name,
                    "confidence": item.get("confidence", 0.9)
                })
            else:
                # Conservative rule: if not clearly in catalog, omit it!
                omitted_items.append({
                    "raw_text": f"{raw_name} ({qty} {unit})",
                    "reason": "Material does not match verified civil carbon catalog standards; omitted to prevent contamination."
                })

        # 2. Record skipped / ambiguous items from LLM
        for amb in doc.get("ambiguous_or_skipped", []):
            omitted_items.append({
                "raw_text": amb.get("raw_text", amb.get("text", "Ambiguous row")),
                "reason": amb.get("reason", "Illegible or ambiguous data omitted for audit accuracy.")
            })

    # Generate partial CSV
    csv_string = generate_partial_csv(verified_materials)

    return {
        "success": True,
        "documents_processed": len(photos_data) if photos_data else 1,
        "documents_summary": documents_summary,
        "verified_materials": verified_materials,
        "verified_count": len(verified_materials),
        "omitted_items": omitted_items,
        "omitted_count": len(omitted_items),
        "csv_content": csv_string
    }
