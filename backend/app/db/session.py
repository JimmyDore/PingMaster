import logging
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Définir le répertoire data en fonction de l'environnement
if os.getenv('ENVIRONMENT') == 'production':
    DATA_DIR = "/app/data"
else:
    DATA_DIR = "./data"  # Chemin relatif pour le développement

try:
    os.makedirs(DATA_DIR, exist_ok=True)
    logger.info(f"Data directory created/verified at: {DATA_DIR}")
except Exception as e:
    logger.error(f"Error creating data directory: {str(e)}")

SQLITE_URL = f"sqlite:///{DATA_DIR}/sql_app.db"
logger.info(f"Using database URL: {SQLITE_URL}")

try:
    engine = create_engine(SQLITE_URL)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    logger.info("Opening new database connection")
    db = SessionLocal()
    try:
        # Vérifier si le fichier existe
        db_file = f"{DATA_DIR}/sql_app.db"
        if os.path.exists(db_file):
            logger.info(f"Database file exists at {db_file}")
            # Vérifier les permissions
            stat = os.stat(db_file)
            logger.info(f"Database file permissions: {oct(stat.st_mode)}")
            logger.info(f"Database file owner: {stat.st_uid}:{stat.st_gid}")
        else:
            logger.warning(f"Database file does not exist at {db_file}")
        
        yield db
        logger.info("Database connection yielded successfully")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
    finally:
        logger.info("Closing database connection")
        db.close()

def init_db():
    logger.info("Initializing database")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")