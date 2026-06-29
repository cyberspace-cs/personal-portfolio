from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
DB_PATH = BASE_DIR / "audit_workbench.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"
CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]
