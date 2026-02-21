"""
Playground Application Configuration
"""
from pydantic_settings import BaseSettings

class AppSettings(BaseSettings):
    APP_TITLE: str = "Revenue Guard Engine — API Playground"
    APP_DESCRIPTION: str = "Revenue Leakage Detection & Validation Engine — Interactive API Playground"
    VERSION: str = "1.0.0"
    DOCS_URL: str = "/playground"
    REDOC_URL: str = "/docs"
    
    # Internal prefixes
    API_PREFIX: str = "/api/v1"
    
    # Data Seeding
    DATA_DIR: str = "generated_data"
    SEED_ON_STARTUP: bool = True

settings = AppSettings()
