import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from uuid import uuid4
from sqlalchemy.orm import Session

from app.db.models import (
    RefreshFrequency,
    Service,
    ServiceStats,
    NotificationPreference,
    NotificationMethod,
    AlertFrequency
)
from app.core.monitor import check_services

@pytest.fixture
def mock_service_notify_recovery_always(test_db: Session):    
    # Service 1: Always notify + recovery
    service1 = Service(
        id=uuid4(),
        name="Service Always",
        url="https://test1.com",
        user_id=uuid4(),
        refresh_frequency=RefreshFrequency.ONE_MINUTE
    )
    pref1 = NotificationPreference(
        service_id=service1.id,
        notification_method=NotificationMethod.SLACK,
        alert_frequency=AlertFrequency.ALWAYS,
        webhook_url="https://hooks.slack.com/test1",
        notify_on_recovery=True
    )
    
    test_db.add_all([service1, pref1])
    test_db.commit()
    
    return service1

@pytest.fixture
def mock_service_notify_no_recovery_daily(test_db: Session):
    service2 = Service(
        id=uuid4(),
        name="Service Daily",
        url="https://test2.com",
        user_id=uuid4(),
        refresh_frequency=RefreshFrequency.ONE_MINUTE
    )
    pref2 = NotificationPreference(
        service_id=service2.id,
        notification_method=NotificationMethod.SLACK,
        alert_frequency=AlertFrequency.DAILY,
        webhook_url="https://hooks.slack.com/test2",
        notify_on_recovery=False
    )

    test_db.add_all([service2, pref2])
    test_db.commit()
    
    return service2

@pytest.mark.asyncio
async def test_first_ping_service_down(test_db: Session, mock_service_notify_recovery_always):
    """Test le premier ping d'un service down"""
    service = mock_service_notify_recovery_always
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (False, None)  # Service down
        mock_slack.return_value = True
        
        await check_services(test_db)
        
        mock_slack.assert_called_once()
        assert "🔴" in str(mock_slack.call_args[0][1])
        assert service.name in str(mock_slack.call_args[0][1])

@pytest.mark.asyncio
async def test_first_ping_service_up(test_db: Session, mock_service_notify_recovery_always):
    """Test le premier ping d'un service up"""
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (True, 100.0)  # Service up
        
        await check_services(test_db)
        
        mock_slack.assert_not_called()

@pytest.mark.asyncio
async def test_transition_up_to_down(test_db: Session, mock_service_notify_recovery_always):
    """Test la transition d'un service de up vers down"""
    service = mock_service_notify_recovery_always
    
    # Créer un historique "up"
    initial_stat = ServiceStats(
        service_id=service.id,
        status=True,
        response_time=100.0,
        ping_date=datetime.utcnow() - timedelta(minutes=5)
    )
    test_db.add(initial_stat)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (False, None)  # Service down
        mock_slack.return_value = True
        
        await check_services(test_db)
        
        mock_slack.assert_called_once()
        assert "🔴" in str(mock_slack.call_args[0][1])

@pytest.mark.asyncio
async def test_recovery_notification(test_db: Session, mock_service_notify_recovery_always):
    """Test la notification de récupération"""
    service = mock_service_notify_recovery_always
    
    # Créer un historique "down"
    initial_stat = ServiceStats(
        service_id=service.id,
        status=False,
        response_time=None,
        ping_date=datetime.utcnow() - timedelta(minutes=5)
    )
    test_db.add(initial_stat)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (True, 100.0)  # Service up
        mock_slack.return_value = True
        
        await check_services(test_db)
        
        mock_slack.assert_called_once()
        assert "🟢" in str(mock_slack.call_args[0][1])

@pytest.mark.asyncio
async def test_no_recovery_notification(test_db: Session, mock_service_notify_no_recovery_daily):
    """Test l'absence de notification de récupération quand désactivée"""
    service = mock_service_notify_no_recovery_daily
    
    # Créer un historique "down"
    initial_stat = ServiceStats(
        service_id=service.id,
        status=False,
        response_time=None,
        ping_date=datetime.utcnow() - timedelta(minutes=5)
    )
    test_db.add(initial_stat)
    test_db.commit()
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (True, 100.0)  # Service up
        
        await check_services(test_db)
        
        mock_slack.assert_not_called()

@pytest.mark.asyncio
async def test_service_down_daily_alert(test_db: Session, mock_service_notify_no_recovery_daily):
    """Test le mode d'alerte quotidien pour un service down"""
    service = mock_service_notify_no_recovery_daily
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (False, None)  # Service down
        mock_slack.return_value = True
        
        # Premier check - devrait envoyer une alerte
        await check_services(test_db)
        assert mock_slack.call_count == 1
        
        # Deuxième check immédiat - ne devrait pas envoyer d'alerte
        await check_services(test_db)
        assert mock_slack.call_count == 1
        
        # Simuler le passage de 24h
        current_time = datetime.utcnow()
        past_time = current_time - timedelta(days=2)
        
        # Update both last_alert_time and last ping_date
        pref = test_db.query(NotificationPreference)\
            .filter(NotificationPreference.service_id == service.id)\
            .first()
        pref.last_alert_time = past_time
        
        # Update the last ping date
        last_stat = test_db.query(ServiceStats)\
            .filter(ServiceStats.service_id == service.id)\
            .order_by(ServiceStats.ping_date.desc())\
            .first()
        last_stat.ping_date = past_time
        
        test_db.add_all([pref, last_stat])
        test_db.commit()
        test_db.refresh(pref)
        test_db.refresh(last_stat)
        
        # Troisième check après 24h - devrait envoyer une nouvelle alerte
        await check_services(test_db)
        assert mock_slack.call_count == 2

@pytest.mark.asyncio
async def test_service_down_always_alert(test_db: Session, mock_service_notify_recovery_always):
    """Test le mode d'alerte constant pour un service down"""
    service = mock_service_notify_recovery_always
    
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        mock_ping.return_value = (False, None)  # Service down
        mock_slack.return_value = True
        
        # Multiple checks - devrait envoyer une alerte à chaque fois
        for _ in range(3):
            # Update the last ping date
            last_stat = test_db.query(ServiceStats)\
                .filter(ServiceStats.service_id == service.id)\
                .order_by(ServiceStats.ping_date.desc())\
                .first()
            if last_stat:
                last_stat.ping_date = datetime.utcnow() - timedelta(minutes=5)
                test_db.add(last_stat)
                test_db.commit()
                test_db.refresh(last_stat)
                
            await check_services(test_db)
        
        assert mock_slack.call_count == 3

@pytest.mark.asyncio
async def test_multiple_services_monitoring(test_db: Session, mock_service_notify_recovery_always, mock_service_notify_no_recovery_daily):
    with patch('app.core.monitor.ping_service', new_callable=AsyncMock) as mock_ping, \
         patch('app.core.notifications.send_slack_notification', new_callable=AsyncMock) as mock_slack:
        
        # Premier check - les deux services down
        mock_ping.side_effect = [(False, None), (False, None)]  # Service 1 & 2 down
        await check_services(test_db)
        assert mock_slack.call_count == 2  # Une alerte pour chaque service
        
        # Deuxième check - toujours down
        mock_ping.side_effect = [(False, None), (False, None)]  # Service 1 & 2 still down
        for service in [mock_service_notify_recovery_always, mock_service_notify_no_recovery_daily]:
            last_stat = test_db.query(ServiceStats)\
                .filter(ServiceStats.service_id == service.id)\
                .order_by(ServiceStats.ping_date.desc())\
                .first()
            if last_stat:
                last_stat.ping_date = datetime.utcnow() - timedelta(minutes=5)
                test_db.add(last_stat)
                test_db.commit()
                test_db.refresh(last_stat)

        await check_services(test_db)
        assert mock_slack.call_count == 3  # Une alerte supplémentaire pour le service "always"
        
        # Troisième check - les services reviennent up
        mock_ping.side_effect = [(True, 100.0), (True, 100.0)]  # Service 1 & 2 up
        for service in [mock_service_notify_recovery_always, mock_service_notify_no_recovery_daily]:
            last_stat = test_db.query(ServiceStats)\
                .filter(ServiceStats.service_id == service.id)\
                .order_by(ServiceStats.ping_date.desc())\
                .first()
            if last_stat:
                last_stat.ping_date = datetime.utcnow() - timedelta(minutes=5)
                last_stat.status = False  # Ensure the previous state is down
                test_db.add(last_stat)
                test_db.commit()
                test_db.refresh(last_stat)
                
        await check_services(test_db)
        assert mock_slack.call_count == 4  # Une seule notification de recovery (service 1)