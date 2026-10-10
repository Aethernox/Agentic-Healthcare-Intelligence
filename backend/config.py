from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    tavily_api_key: str = ""
    databricks_token: str = ""
    databricks_host: str = ""

    # Database — defaults to SQLite for local dev, set to Postgres URL in production
    database_url: str = "sqlite:///./medmap.db"
    redis_url: str = "redis://localhost:6379"

    # Mosaic AI Vector Search (Databricks)
    vector_search_endpoint: str = ""
    vector_search_index: str = "medmap.hospitals.embeddings"

    # MLflow
    mlflow_tracking_uri: str = "databricks"
    mlflow_experiment_name: str = "/medmap/agent-runs"

    # App
    allowed_origins: List[str] = ["http://localhost:5173", "https://medmap.vercel.app"]
    environment: str = "development"
    log_level: str = "INFO"

    # Trust scoring thresholds
    trust_high_threshold: int = 75
    trust_medium_threshold: int = 40
    tavily_trigger_threshold: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
