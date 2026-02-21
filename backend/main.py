from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.audit_controller import router as audit_router
from backend.api.crm_simulator import router as crm_router
from backend.api.finance_simulator import finance_router
from backend.api.validation_controller import validation_router

app = FastAPI(
    title="Revenue Guard Engine API",
    description="Intelligent Reconciliation & Validation System Framework",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Epic routers here
app.include_router(audit_router)
app.include_router(crm_router)
app.include_router(finance_router)
app.include_router(validation_router)

@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "Revenue Guard Engine API is running"}
