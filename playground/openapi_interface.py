"""
Main OpenAPI Playground Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from playground.app_config import settings
from playground.startup import startup_event, shutdown_event
from playground.system_controller import router as system_router

# Import Production-Grade Routers
from backend.api.ghl_connector import router as crm_router
from backend.api.qb_engine import finance_router
from backend.api.validation_controller import validation_router
from backend.api.audit_controller import router as audit_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register Event Handlers
    await startup_event()
    yield
    await shutdown_event()

app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    lifespan=lifespan,
    openapi_tags=[
        {"name": "GoHighLevel Connector", "description": "GHL-style CRM operations"},
        {"name": "QuickBooks Online Engine", "description": "QuickBooks-style accounting operations"},
        {"name": "Validation & Risk Scoring Engine", "description": "Risk scoring and reconciliation"},
        {"name": "Audit Log Inspector", "description": "Audit trail inspection"},
        {"name": "System", "description": "Health, configuration, and data management"},
    ],
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(crm_router, prefix=settings.API_PREFIX)
app.include_router(finance_router, prefix=settings.API_PREFIX)
app.include_router(validation_router, prefix=settings.API_PREFIX)
app.include_router(audit_router, prefix=settings.API_PREFIX)
app.include_router(system_router, prefix=settings.API_PREFIX)


@app.get("/", include_in_schema=False)
async def root():
    return {
        "message": "Revenue Guard Engine API Playground",
        "playground_url": settings.DOCS_URL,
        "api_reference": settings.REDOC_URL
    }
