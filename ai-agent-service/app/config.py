import os
from pydantic import BaseModel

class Settings(BaseModel):
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    OLLAMA_EMBEDDING_MODEL: str = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
    CHROMA_HOST: str = os.getenv("CHROMA_HOST", "chroma")
    CHROMA_PORT: int = int(os.getenv("CHROMA_PORT", "8000"))
    CHROMA_COLLECTION: str = os.getenv("CHROMA_COLLECTION", "esport-rules")
    BACKEND_API_URL: str = os.getenv("BACKEND_API_URL", "http://backend:8080/api")
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "admin123")
    APP_PORT: int = int(os.getenv("PORT", "8001"))

settings = Settings()
