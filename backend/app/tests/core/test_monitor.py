import uuid
import pytest
from datetime import datetime, timedelta
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from httpx import TimeoutException, HTTPError
from app.core.monitor import (
    ping_service,
    process_service_batch,
    check_services,
    should_check_service,
    MAX_CONCURRENT_REQUESTS
)
from app.db.models import Service, ServiceStats, RefreshFrequency

# Fixtures
@pytest.fixture
def mock_service():
    return Service(
        id=uuid.uuid4(),
        name="Test Service",
        url="https://example.com",
        refresh_frequency=RefreshFrequency.ONE_MINUTE
    )

@pytest.fixture
def mock_services():
    return [
        Service(
            id=uuid.uuid4(),
            name=f"Test Service {i}",
            url=f"https://example{i}.com",
            refresh_frequency=RefreshFrequency.ONE_MINUTE
        )
        for i in range(5)
    ]

# Tests pour ping_service
@pytest.mark.asyncio
async def test_ping_service_success(mock_service):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = Mock(status_code=200)
        status, response_time = await ping_service(mock_service)
        
        assert status is True
        assert isinstance(response_time, float)
        assert response_time > 0

@pytest.mark.asyncio
async def test_ping_service_failure(mock_service):
    with patch('httpx.AsyncClient.get') as mock_get:
        mock_get.return_value = Mock(status_code=500)
        status, response_time = await ping_service(mock_service)
        
        assert status is False
        assert isinstance(response_time, float)

@pytest.mark.asyncio
async def test_ping_service_timeout(mock_service):
    with patch('httpx.AsyncClient.get', side_effect=TimeoutException("Timeout")):
        status, response_time = await ping_service(mock_service)
        
        assert status is False
        assert response_time is None

@pytest.mark.asyncio
async def test_ping_service_connection_error(mock_service):
    with patch('httpx.AsyncClient.get', side_effect=HTTPError("Connection failed")):
        status, response_time = await ping_service(mock_service)
        
        assert status is False
        assert response_time is None

# Tests pour process_service_batch
@pytest.mark.asyncio
async def test_process_service_batch(mock_services):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = (True, 100.0)
        results = await process_service_batch(mock_services, semaphore)
        
        assert len(results) == len(mock_services)
        for result in results:
            assert isinstance(result, ServiceStats)
            assert result.status is True
            assert result.response_time == 100.0

@pytest.mark.asyncio
async def test_process_service_batch_with_mixed_results(mock_services):
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    
    async def mock_ping_with_varying_results(service):
        if "1" in service.url:
            return False, None
        return True, 100.0
    
    with patch('app.core.monitor.ping_service', side_effect=mock_ping_with_varying_results):
        results = await process_service_batch(mock_services, semaphore)
        
        success_count = len([r for r in results if r.status])
        failure_count = len([r for r in results if not r.status])
        assert success_count + failure_count == len(mock_services)

# Tests pour should_check_service
def test_should_check_service_no_previous_stats(mock_service):
    current_time = datetime.utcnow()
    assert should_check_service(mock_service, None, current_time) is True

def test_should_check_service_due_for_check():
    service = Mock(refresh_frequency=RefreshFrequency.ONE_MINUTE)
    last_stat = Mock(ping_date=datetime.utcnow() - timedelta(minutes=2))
    current_time = datetime.utcnow()
    
    assert should_check_service(service, last_stat, current_time) is True

def test_should_check_service_not_due():
    service = Mock(refresh_frequency=RefreshFrequency.ONE_HOUR)
    last_stat = Mock(ping_date=datetime.utcnow() - timedelta(minutes=30))
    current_time = datetime.utcnow()
    
    assert should_check_service(service, last_stat, current_time) is False

# Tests pour check_services
@pytest.mark.asyncio
async def test_check_services_empty_db(test_db):
    await check_services(test_db)
    stats = test_db.query(ServiceStats).all()
    assert len(stats) == 0

@pytest.mark.asyncio
async def test_check_services_with_services(test_db, mock_services):
    # Ajoute les services de test à la base de données
    for service in mock_services:
        test_db.add(service)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = (True, 100.0)
        await check_services(test_db)
        
        stats = test_db.query(ServiceStats).all()
        assert len(stats) == len(mock_services)
        for stat in stats:
            assert stat.status is True
            assert stat.response_time == 100.0

@pytest.mark.asyncio
async def test_check_services_with_errors(test_db, mock_services):
    # Ajoute les services de test à la base de données
    for service in mock_services:
        test_db.add(service)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', side_effect=Exception("Test error")):
        await check_services(test_db)
        
        # Vérifie que la transaction a été rollback
        stats = test_db.query(ServiceStats).all()
        assert len(stats) == 0

@pytest.mark.asyncio
async def test_check_services_respects_frequency(test_db, mock_service):
    test_db.add(mock_service)
    
    # Ajoute une stat récente
    recent_stat = ServiceStats(
        service_id=mock_service.id,
        status=True,
        response_time=100.0,
        ping_date=datetime.utcnow() - timedelta(seconds=30)
    )
    test_db.add(recent_stat)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping:
        await check_services(test_db)
        
        # Vérifie que le service n'a pas été re-vérifié
        assert mock_ping.call_count == 0
        stats = test_db.query(ServiceStats).all()
        assert len(stats) == 1  # Seulement la stat initiale

@pytest.mark.asyncio
async def test_check_services_batch_processing(test_db):
    # Crée 100 services pour tester le traitement par lots
    services = [
        Service(
            id=uuid.uuid4(),
            name=f"Test Service {i}",
            url=f"https://example{i}.com",
            refresh_frequency=RefreshFrequency.ONE_MINUTE
        )
        for i in range(100)
    ]
    
    for service in services:
        test_db.add(service)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping:
        mock_ping.return_value = (True, 100.0)
        await check_services(test_db)
        
        stats = test_db.query(ServiceStats).all()
        assert len(stats) == 100
        # Vérifie que les services ont été traités par lots
        assert mock_ping.call_count == 100 