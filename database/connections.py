from database.models import init_db
from config import config

_db_session = None

def get_db_session():
    """Get database session (singleton pattern)"""
    global _db_session
    if _db_session is None:
        SessionLocal = init_db(config.DATABASE_URL)
        _db_session = SessionLocal()
    return _db_session
