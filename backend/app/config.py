from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(BASE_DIR / ".env", ".env"), extra="ignore")
    database_url: str = "postgresql+psycopg://procure:procure@localhost:5432/procureagent"
    uploads_dir: Path = BASE_DIR / "data" / "uploads"
    llm_api_key: str = ""
    llm_model: str = ""
    seuil_approbation: float = 1000.0
    seuil_confiance_ocr: float = 0.85
    max_etapes: int = 40  # garde-fou anti-boucle


settings = Settings()
