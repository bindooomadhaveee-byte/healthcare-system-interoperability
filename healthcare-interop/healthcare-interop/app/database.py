"""
Database configuration.

Uses SQLite for simplicity so the project runs with zero external
dependencies. Swap SQLALCHEMY_DATABASE_URL for Postgres/MySQL in a real
deployment (e.g. "postgresql://user:pass@host/dbname").
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./healthcare_interop.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency that yields a DB session and closes it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
