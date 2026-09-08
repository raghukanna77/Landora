from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings
import os

database_url = settings.get_database_url()

connect_args = {}
if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# Render Postgres requires SSL in some cases; SQLAlchemy handles via URL
engine = create_engine(database_url, connect_args=connect_args, echo=False, future=True, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create tables if not exist. For Render: ensure PostGIS extension optional."""
    # Try to enable PostGIS if postgres, but don't fail if not available
    if database_url.startswith("postgresql"):
        try:
            with engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
        except Exception:
            pass  # PostGIS not available on Render free Postgres, fallback to Text geometry
    Base.metadata.create_all(bind=engine)
