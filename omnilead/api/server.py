"""
FastAPI Application Server
===========================
Exposes OmniLead-AI as a production-grade REST API with:
  - POST /api/v1/enrich      — Single lead enrichment
  - POST /api/v1/batch       — CSV batch upload and processing
  - GET  /api/v1/health      — System healthcheck
  - GET  /                   — Interactive live dashboard (HTML)
"""
from __future__ import annotations

import asyncio
import csv
import io
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel

from omnilead.config import settings
from omnilead.core.pipeline import process_single_lead, run_pipeline
from omnilead.models.schemas import EnrichedLead, RawLead

logger = logging.getLogger(__name__)

app = FastAPI(
    title="OmniLead-AI",
    description=(
        "Async B2B Lead Scraping, DNS Email Verification & Gemini AI Personalization Pipeline.\n\n"
        "Built for lead generation agencies, outbound sales teams, and automation-first freelancers."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# API Models
# ─────────────────────────────────────────────────────────────────────────────

class EnrichRequest(BaseModel):
    company_name: str
    website: str
    prospect_name: str = ""
    prospect_email: str = ""
    prospect_role: str = ""
    niche: str = ""


class HealthResponse(BaseModel):
    status: str
    version: str
    mock_mode: bool
    ai_enabled: bool
    gemini_model: str
    timestamp: str


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/api/v1/health", response_model=HealthResponse, tags=["System"])
async def health():
    """Returns system configuration and readiness status."""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        mock_mode=settings.mock_mode,
        ai_enabled=settings.ai_enabled,
        gemini_model=settings.gemini_model,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.post("/api/v1/enrich", tags=["Pipeline"])
async def enrich_single(request: EnrichRequest):
    """
    Enrich a single lead through the full OmniLead-AI pipeline.

    Returns a fully populated EnrichedLead JSON object in real-time.
    """
    raw = RawLead(**request.model_dump())
    try:
        enriched = await process_single_lead(raw)
        return JSONResponse(content=json.loads(enriched.model_dump_json()))
    except Exception as exc:
        logger.error(f"Enrichment error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/v1/batch", tags=["Pipeline"])
async def batch_process(file: UploadFile = File(...)):
    """
    Upload a CSV file of raw leads for batch enrichment.

    Returns a downloadable enriched CSV file with all AI metadata columns.
    """
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    raw_leads = []
    for row in reader:
        raw_leads.append(RawLead(
            company_name=row.get("company_name", row.get("Company", "")).strip(),
            website=row.get("website", row.get("Website", "")).strip(),
            prospect_name=row.get("prospect_name", row.get("Name", "")).strip(),
            prospect_email=row.get("prospect_email", row.get("Email", "")).strip(),
            prospect_role=row.get("prospect_role", row.get("Role", "")).strip(),
            niche=row.get("niche", row.get("Niche", "")).strip(),
        ))

    if not raw_leads:
        raise HTTPException(status_code=400, detail="CSV file is empty or malformed.")

    results = await run_pipeline(raw_leads)

    # Stream CSV back
    output = io.StringIO()
    fieldnames = list(results[0].to_csv_row().keys()) if results else []
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for lead in results:
        writer.writerow(lead.to_csv_row())

    output.seek(0)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=omnilead_enriched_{ts}.csv"},
    )


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Serve the interactive OmniLead-AI live dashboard."""
    dashboard_path = Path(__file__).parent.parent / "static" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content=_fallback_dashboard_html())


def _fallback_dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OmniLead-AI Dashboard</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  body{background:#0d1117;color:#e6edf3;font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2rem;padding:2rem}
  h1{font-size:2.5rem;font-weight:700;background:linear-gradient(135deg,#58a6ff,#3fb950);-webkit-background-clip:text;-webkit-text-fill-color:transparent}
  .badge{background:#21262d;border:1px solid #30363d;border-radius:6px;padding:.5rem 1rem;font-size:.85rem;color:#8b949e}
  .badge span{color:#3fb950;font-weight:600}
  .links{display:flex;gap:1rem;flex-wrap:wrap;justify-content:center}
  a{background:#21262d;border:1px solid #30363d;color:#58a6ff;padding:.75rem 1.5rem;border-radius:8px;text-decoration:none;font-weight:500;transition:border-color .2s}
  a:hover{border-color:#58a6ff}
  .subtitle{color:#8b949e;font-size:1rem;text-align:center;max-width:600px;line-height:1.6}
</style>
</head>
<body>
<h1>OmniLead-AI</h1>
<p class="subtitle">Async B2B Lead Scraping · DNS Email Verification · Gemini AI Personalization · CRM Dispatch</p>
<div class="badge">Status: <span>ONLINE</span></div>
<div class="links">
  <a href="/docs">📖 API Docs (Swagger)</a>
  <a href="/redoc">📋 ReDoc</a>
  <a href="/api/v1/health">❤️ Health Check</a>
</div>
</body>
</html>"""
