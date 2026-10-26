import os

from dotenv import load_dotenv

# Looks for a .env file in this folder or any parent folder (so the project-root .env works).
load_dotenv()


class Settings:
    def __init__(self) -> None:
        self.database_url = os.getenv(
            "DATABASE_URL", "postgresql://chrono:chrono@localhost:5433/chronorag"
        )
        self.llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
                self.gemini_model = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.anthropic_model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.embedding_model = os.getenv(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.cors_origins = [
            o.strip()
            for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]


settings = Settings()
