"""
FastAPI Application for Concrete Construction Embodied Carbon Digital Twin.
Serves the web dashboard, REST API endpoints, Excel/CSV ingestion, and report generation.
"""

import os
import io
import json
import base64
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from engine.digital_twin import ConcreteDigitalTwin
from engine.data_manager import DataManager
from engine.carbon_calculator import safe_float
from engine.emission_database import get_full_emission_catalog
from engine.vision_ocr import (
    is_groq_configured,
    get_groq_api_key,
    set_groq_api_key,
    process_challan_photos,
    DEFAULT_VISION_MODEL
)
from sample_data.generate_samples import get_default_project_data

# Initialize app
app = FastAPI(
    title="Digital Twin Embodied Carbon Monitoring System",
    description="Dynamic monitoring and visualization of embodied carbon during concrete construction (EN 15978 / ISO 21930)",
    version="1.0.0"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

# Singleton Digital Twin instance in memory
twin = ConcreteDigitalTwin()

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Render the main interactive Digital Twin web dashboard."""
    return templates.TemplateResponse(request, "index.html")

@app.get("/presentation", response_class=HTMLResponse)
async def serve_presentation():
    """Render the presentation slide deck."""
    presentation_path = os.path.join(BASE_DIR, "presentation.html")
    with open(presentation_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

@app.get("/api/project")
async def get_project_state():
    """Return the current comprehensive state of the Digital Twin."""
    return JSONResponse(content=twin.get_full_state())

@app.post("/api/upload")
async def upload_file(request: Request):
    """
    Handle Excel (.xlsx) or CSV file uploads.
    Accepts JSON payload: { "filename": "...", "data": "base64..." }
    """
    try:
        body = await request.json()
        filename = body.get("filename", "uploaded_file.xlsx")
        b64_data = body.get("data", "")
        
        if not b64_data:
            raise HTTPException(status_code=400, detail="No file data provided.")

        parsed_data, msg = DataManager.parse_uploaded_file(
            filename=filename,
            file_bytes_or_b64=b64_data,
            current_state=twin.get_full_state()
        )
        twin.load_state(parsed_data, snapshot_label=f"Uploaded: {filename}")
        
        return JSONResponse(content={
            "success": True,
            "message": msg,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/reset")
async def reset_project():
    """Reset the Digital Twin to default demonstration dataset."""
    twin.reset_to_default()
    return JSONResponse(content={
        "success": True,
        "message": "Reset to default concrete package activity data.",
        "project_state": twin.get_full_state()
    })

@app.post("/api/update/material")
async def update_material(request: Request):
    """Update a single material item by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        updates = body.get("updates", {})
        reason = body.get("reason", "Material Parameter Edit")
        
        success = twin.update_material(index, updates, reason)
        if not success:
            raise HTTPException(status_code=404, detail="Material index out of bounds.")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Updated material #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/update/transport")
async def update_transport(request: Request):
    """Update a transport record by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        updates = body.get("updates", {})
        reason = body.get("reason", "Transport Parameter Edit")
        
        success = twin.update_transport(index, updates, reason)
        if not success:
            raise HTTPException(status_code=404, detail="Transport index out of bounds.")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Updated transport #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/update/equipment")
async def update_equipment(request: Request):
    """Update an equipment record by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        updates = body.get("updates", {})
        reason = body.get("reason", "Equipment Parameter Edit")
        
        success = twin.update_equipment(index, updates, reason)
        if not success:
            raise HTTPException(status_code=404, detail="Equipment index out of bounds.")
        
        return JSONResponse(content={
            "success": True,
            "message": f"Updated equipment #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/update/meta")
async def update_meta(request: Request):
    """Update project-level metadata (concrete volume, grade, budget)."""
    try:
        body = await request.json()
        twin.update_project_meta(body)
        return JSONResponse(content={
            "success": True,
            "message": "Project metadata updated.",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/emission-factors")
async def get_emission_factors():
    """Return central emission factor catalog and standard references [1]–[6]."""
    return JSONResponse(content=get_full_emission_catalog())

@app.post("/api/stages/add")
async def add_stage(request: Request):
    """Add a new continuous periodic site log milestone."""
    try:
        body = await request.json()
        new_stage = twin.add_periodic_stage(body)
        return JSONResponse(content={
            "success": True,
            "message": f"Logged {new_stage['name']}",
            "stage": new_stage,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/stages/select")
async def select_stage(request: Request):
    """Switch active stage in digital twin to inspect or edit its specific logs."""
    try:
        body = await request.json()
        stage_id = int(body.get("stage_id", 1))
        success = twin.select_stage(stage_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stage ID not found.")
        return JSONResponse(content={
            "success": True,
            "active_stage_id": stage_id,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/stages/delete")
async def delete_stage(request: Request):
    """Remove a site progress stage by stage_id."""
    try:
        body = await request.json()
        stage_id = int(body.get("stage_id", -1))
        success = twin.delete_stage(stage_id)
        if not success:
            raise HTTPException(status_code=404, detail="Stage ID not found.")
        return JSONResponse(content={
            "success": True,
            "message": f"Removed stage #{stage_id}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/stages/update-status")
async def update_stage_status_endpoint(request: Request):
    """Update status of a site milestone log (Completed, In Progress, Scheduled)."""
    try:
        body = await request.json()
        stage_id = int(body.get("stage_id", -1))
        status = str(body.get("status", "In Progress")).strip()
        if status not in ("Completed", "In Progress", "Scheduled"):
            raise HTTPException(status_code=400, detail="Invalid status. Must be Completed, In Progress, or Scheduled.")
        success = twin.update_stage_status(stage_id, status)
        if not success:
            raise HTTPException(status_code=404, detail="Stage ID not found.")
        return JSONResponse(content={
            "success": True,
            "stage_id": stage_id,
            "status": status,
            "project_state": twin.get_full_state()
        })
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/materials/add")
async def add_material(request: Request):
    """Add a new material entry to materials log."""
    try:
        body = await request.json()
        new_mat = twin.add_material(body)
        return JSONResponse(content={
            "success": True,
            "message": f"Added material {new_mat['material_name']}",
            "material": new_mat,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/materials/delete")
async def delete_material(request: Request):
    """Remove a material entry by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        success = twin.delete_material(index)
        if not success:
            raise HTTPException(status_code=404, detail="Material index out of bounds.")
        return JSONResponse(content={
            "success": True,
            "message": f"Removed material #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/transport/add")
async def add_transport(request: Request):
    """Add a new transport entry."""
    try:
        body = await request.json()
        new_tr = twin.add_transport(body)
        return JSONResponse(content={
            "success": True,
            "message": f"Added transport {new_tr['material_name']}",
            "transport": new_tr,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/transport/delete")
async def delete_transport(request: Request):
    """Remove a transport entry by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        success = twin.delete_transport(index)
        if not success:
            raise HTTPException(status_code=404, detail="Transport index out of bounds.")
        return JSONResponse(content={
            "success": True,
            "message": f"Removed transport #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/equipment/add")
async def add_equipment(request: Request):
    """Add a new equipment entry."""
    try:
        body = await request.json()
        new_eq = twin.add_equipment(body)
        return JSONResponse(content={
            "success": True,
            "message": f"Added equipment {new_eq['equipment_name']}",
            "equipment": new_eq,
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/equipment/delete")
async def delete_equipment(request: Request):
    """Remove an equipment entry by index."""
    try:
        body = await request.json()
        index = int(body.get("index", -1))
        success = twin.delete_equipment(index)
        if not success:
            raise HTTPException(status_code=404, detail="Equipment index out of bounds.")
        return JSONResponse(content={
            "success": True,
            "message": f"Removed equipment #{index}",
            "project_state": twin.get_full_state()
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/what-if")
async def simulate_what_if(request: Request):
    """Simulate green decarbonization interventions and return comparative metrics."""
    try:
        modifications = await request.json()
        sim_result = twin.simulate_what_if(modifications)
        
        # If user explicitly requests to commit this scenario as active state
        if modifications.get("commit_to_twin", False):
            label = modifications.get("scenario_name", "What-If Scenario Applied")
            twin.load_state({
                "project_meta": twin.project_meta,
                "materials": sim_result["simulated_summary"]["materials_module"]["items"],
                "transport": sim_result["simulated_summary"]["transport_module"]["items"],
                "equipment": sim_result["simulated_summary"]["equipment_module"]["items"],
                "stages": twin.stages
            }, snapshot_label=f"Applied: {label}")
            sim_result["committed"] = True
            sim_result["updated_project_state"] = twin.get_full_state()

        return JSONResponse(content={"success": True, "result": sim_result})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/snapshot")
async def create_snapshot(request: Request):
    """Create a manual user-named version snapshot."""
    try:
        body = await request.json()
        label = body.get("label", "Manual User Checkpoint")
        author = body.get("author", "User")
        snap = twin.create_snapshot(label=label, author=author)
        return JSONResponse(content={"success": True, "snapshot": snap, "snapshots": twin.snapshots})
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.get("/api/export/excel")
async def export_excel():
    """Stream generated multi-sheet Excel calculation report."""
    excel_bytes = DataManager.export_project_to_excel(twin.get_full_state())
    headers = {
        "Content-Disposition": 'attachment; filename="Concrete_Embodied_Carbon_Twin_Report.xlsx"'
    }
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@app.get("/api/templates/download")
async def download_template():
    """Stream empty template Excel file."""
    tmpl_path = os.path.join(STATIC_DIR, "templates", "Concrete_Twin_Template.xlsx")
    if not os.path.exists(tmpl_path):
        from sample_data.generate_samples import generate_sample_files
        generate_sample_files(BASE_DIR)

    with open(tmpl_path, "rb") as f:
        content = f.read()
    headers = {
        "Content-Disposition": 'attachment; filename="Concrete_Twin_Template.xlsx"'
    }
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers=headers
    )

@app.get("/api/ocr/status")
async def get_ocr_status():
    """Check whether Groq Vision API key is configured."""
    configured = is_groq_configured()
    masked = None
    key = get_groq_api_key()
    if key and len(key) > 8:
        masked = f"{key[:4]}...{key[-4:]}"
    return JSONResponse(content={
        "configured": configured,
        "masked_key": masked,
        "model": DEFAULT_VISION_MODEL
    })

@app.post("/api/ocr/set-key")
async def save_ocr_key(request: Request):
    """Save or update Groq API key in memory and local .env."""
    try:
        body = await request.json()
        api_key = str(body.get("api_key", "")).strip()
        if not api_key:
            raise HTTPException(status_code=400, detail="API key cannot be empty.")
        set_groq_api_key(api_key)
        return JSONResponse(content={
            "success": True,
            "message": "Groq API key saved successfully.",
            "configured": True
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

@app.post("/api/ocr/parse-photos")
async def parse_challan_photos_endpoint(request: Request):
    """
    Process one or multiple uploaded challan / invoice photos using Groq Vision OCR.
    Extracts confirmed material line items and skips ambiguous lines.
    Optionally auto-adds verified items to the currently active stage.
    """
    try:
        body = await request.json()
        photos = body.get("photos", [])
        auto_add = bool(body.get("auto_add", False))

        if not photos:
            raise HTTPException(status_code=400, detail="No photo files provided.")

        if not is_groq_configured():
            return JSONResponse(status_code=400, content={
                "success": False,
                "error": "Groq API key not configured. Please provide your GROQ_API_KEY in the settings.",
                "requires_key": True
            })

        photos_data = []
        for p in photos:
            fname = p.get("name", "challan.jpg")
            raw_b64 = p.get("data", "")
            mime = p.get("type", "image/jpeg")
            if "," in raw_b64:
                raw_b64 = raw_b64.split(",", 1)[1]
            p_bytes = base64.b64decode(raw_b64)
            photos_data.append((fname, p_bytes, mime))

        result = process_challan_photos(photos_data)

        if auto_add and result.get("verified_materials"):
            twin.add_materials_batch(
                result["verified_materials"], 
                snapshot_label=f"OCR Ingestion: {len(result['verified_materials'])} materials"
            )
            result["added_to_stage"] = True
            result["project_state"] = twin.get_full_state()
        else:
            result["added_to_stage"] = False

        return JSONResponse(content=result)
    except HTTPException as he:
        return JSONResponse(status_code=he.status_code, content={"success": False, "error": he.detail})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})

@app.post("/api/ocr/add-verified")
async def add_verified_ocr_items(request: Request):
    """Add verified items extracted from OCR into the active digital twin milestone log."""
    try:
        body = await request.json()
        materials = body.get("materials", [])
        if not materials:
            raise HTTPException(status_code=400, detail="No materials to add.")

        added_count = twin.add_materials_batch(
            materials,
            snapshot_label=f"OCR Ingestion: {len(materials)} materials"
        )

        return JSONResponse(content={
            "success": True,
            "added_count": added_count,
            "project_state": twin.get_full_state(),
            "message": f"Successfully added {added_count} verified material(s) to active milestone log."
        })
    except Exception as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
