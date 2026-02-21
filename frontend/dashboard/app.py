import os
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from backend.api.validation_controller import _get_engine
from visualization.chart_exporter import ChartExporter

app = FastAPI(title="Revenue Guard Dashboard")

# Setup templates and static files
# Get absolute path for reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Ensure static and charts directories exist
os.makedirs(os.path.join(BASE_DIR, "static/charts"), exist_ok=True)

app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

@app.get("/")
async def dashboard(request: Request):
    engine = _get_engine()
    
    # Ensure some results exist for the dashboard
    results = engine.get_all_results()
    if not results:
        # Trigger a full scan if no results
        results = engine.reconcile_all()
        
    # Always try to export charts if they don't exist
    chart_dir = os.path.join(BASE_DIR, "static/charts")
    if not os.path.exists(os.path.join(chart_dir, "risk_distribution.png")):
        exporter = ChartExporter(chart_dir)
        exporter.export_all(results)
    
    stats = engine.get_statistics()
    
    # Get high-risk transactions
    high_risk = [r for r in results if r.risk_classification == 'critical']
    high_risk = sorted(high_risk, key=lambda x: x.risk_score, reverse=True)[:10]

    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": stats,
        "high_risk": high_risk,
        "last_scan": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

@app.post("/refresh")
async def refresh_dashboard():
    engine = _get_engine()
    results = engine.reconcile_all()
    chart_dir = os.path.join(BASE_DIR, "static/charts")
    exporter = ChartExporter(chart_dir)
    exporter.export_all(results)
    return {"status": "success", "message": "Dashboard assets refreshed"}
