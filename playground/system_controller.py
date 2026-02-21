"""
System Controller
"""
from fastapi import APIRouter, BackgroundTasks
from playground.app_config import settings
from backend.api.crm_simulator import get_store as get_crm_store
from backend.api.finance_simulator import get_store as get_finance_store
from backend.data.synthetic_data_generator import SyntheticDataGenerator
import time

router = APIRouter(prefix="/system", tags=["System"])

START_TIME = time.time()

@router.get("/health")
async def health_check():
    """Returns the health status of the API."""
    return {"status": "ok", "timestamp": time.time()}

@router.get("/info")
async def system_info():
    """Returns system version, uptime, and configuration."""
    return {
        "title": settings.APP_TITLE,
        "version": settings.VERSION,
        "uptime_seconds": int(time.time() - START_TIME),
        "data_directory": settings.DATA_DIR
    }

@router.post("/reset")
async def reset_data():
    """Resets all in-memory data stores to the state of the seed files on disk."""
    crm_store = get_crm_store()
    finance_store = get_finance_store()
    
    crm_store.load_seed_data()
    finance_store._load_seed_data()
    
    return {"status": "success", "message": "Stores reset to seed data."}

@router.post("/seed")
async def reseed_data(background_tasks: BackgroundTasks):
    """
    Trigger a fresh synthetic data generation and reload stores.
    This is an expensive operation and is run in the background.
    """
    def generate_and_reload():
        generator = SyntheticDataGenerator()
        dataset = generator.generate()
        generator.save(dataset, output_dir=settings.DATA_DIR)
        
        crm_store = get_crm_store()
        finance_store = get_finance_store()
        crm_store.load_seed_data()
        finance_store._load_seed_data()

    background_tasks.add_task(generate_and_reload)
    return {"status": "accepted", "message": "Reseeding started in background."}
