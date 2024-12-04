import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.session import Base, get_db
from app.main import app

SQLITE_TEST_URL = "sqlite:///./test.db"

@pytest.fixture
def test_db():
    """Fixture that provides a test database session"""
    engine = create_engine(SQLITE_TEST_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Créer et retourner une session de test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(test_db):
    """Fixture that provides a test client with a test database"""
    def override_get_db():
        try:
            yield test_db
        finally:
            test_db.close()
            
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)