import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from app.db.session import Base, get_db
from app.main import app
from app.db.models import RefreshFrequency, User, Service
from app.core.auth import get_password_hash, create_access_token
from datetime import timedelta
from uuid import uuid4

SQLITE_TEST_URL = "sqlite:///./test.db"

@pytest.fixture
def test_db():
    """Fixture that provides a test database session"""
    engine = create_engine(SQLITE_TEST_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_user(test_db):
    """Create a test user and return it"""
    user = User(
        id=uuid.UUID("a3ded56b-a4c6-49ef-8953-b8f1b0648145"),
        username="testuser@example.com",
        hashed_password=get_password_hash("testpass")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_user2(test_db):
    """Create a second test user for testing isolation"""
    user = User(
        id=uuid.UUID("667a2f85-9d9a-46dd-9ef8-e92dbb49b2df"),
        username="testuser2",
        hashed_password=get_password_hash("testpass2")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def test_user3(test_db):
    """Create a third test user for testing isolation"""
    user = User(
        id=uuid4(),
        username="testuser3",
        hashed_password=get_password_hash("testpass3")
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user"""
    access_token = create_access_token(
        data={"sub": str(test_user.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def auth_headers2(test_user2):
    """Generate authentication headers for second test user"""
    access_token = create_access_token(
        data={"sub": str(test_user2.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def auth_headers3(test_user3):
    """Generate authentication headers for third test user"""
    access_token = create_access_token(
        data={"sub": str(test_user3.id)},
        expires_delta=timedelta(minutes=30)
    )
    return {"Authorization": f"Bearer {access_token}"}

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

@pytest.fixture
def mock_services(test_user):
    """Create mock services with a valid user_id"""
    return [
        Service(
            id=uuid4(),
            name=f"Test Service {i}",
            url=f"https://example{i}.com",
            refresh_frequency=RefreshFrequency.ONE_MINUTE,
            user_id=test_user.id
        )
        for i in range(3)
    ]