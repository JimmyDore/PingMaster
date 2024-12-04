from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# Créer le répertoire data s'il n'existe pas
DATA_DIR = "/app/data"
os.makedirs(DATA_DIR, exist_ok=True)

SQLITE_URL = f"sqlite:///{DATA_DIR}/sql_app.db"

engine = create_engine(SQLITE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)