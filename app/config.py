from pydantic_settings import BaseSettings
from typing import Literal
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    
    app_env: Literal["development", "production", "testing"] = "development"
    log_level: str = "INFO"
    max_upload_size: int = 10485760  # 10MB
    
    chroma_persist_directory: str = "./data/chroma"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    llm_provider: Literal["openai", "anthropic"] = "openai"
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.7
    max_tokens: int = 1000
    
    top_k_results: int = 5
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist."""
        Path(self.chroma_persist_directory).mkdir(parents=True, exist_ok=True)
        Path("./data/uploads").mkdir(parents=True, exist_ok=True)
        Path("./logs").mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()