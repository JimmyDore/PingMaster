import logging
from datetime import datetime, timedelta
import httpx
from app.db.models import NotificationMethod, AlertFrequency, NotificationPreference, ServiceStats
from typing import Optional

logger = logging.getLogger(__name__)

async def send_slack_notification(webhook_url: str, message: str | dict) -> bool:
    """Send a Slack notification via webhook
    
    Args:
        webhook_url: The Slack webhook URL
        message: Either a string for simple messages or a dict for block-structured messages
    """
    try:
        async with httpx.AsyncClient() as client:
            payload = {"text": message} if isinstance(message, str) else message
            response = await client.post(webhook_url, json=payload)
            if response.status_code != 200:
                logger.error(f"Slack API error: {response.status_code} - {response.text}")
            return response.status_code == 200
    except Exception as e:
        logger.error(f"Error sending Slack notification: {str(e)}")
        return False

async def should_send_notification(
    preference: NotificationPreference,
    previous_stat: Optional[ServiceStats] = None,
    new_stat: Optional[ServiceStats] = None
) -> bool:
    """Détermine si une notification doit être envoyée"""
    
    if not preference:
        return False
    
    # Cas de recovery (service revient en ligne)
    if previous_stat and previous_stat.is_down and not new_stat.is_down and preference.notify_on_recovery:
        return True
        
    if not new_stat.is_down:
        return False
    
    if not previous_stat:
        return True
        
    if preference.alert_frequency == AlertFrequency.ALWAYS:
        return True
        
    if preference.alert_frequency == AlertFrequency.DAILY:
        if not preference.last_alert_time:
            return True
            
        time_since_last_alert = datetime.utcnow() - preference.last_alert_time
        return time_since_last_alert > timedelta(days=1)
    
    return False

async def send_service_notification(
    db_session,
    service_name: str,
    is_down: bool,
    new_stat: ServiceStats,
    previous_stat: Optional[ServiceStats] = None,
    preference: Optional[NotificationPreference] = None,
    service_url: Optional[str] = None,
) -> bool:
    """Envoie une notification pour un service selon ses préférences"""
    if not preference:
        return False

    should_notify = await should_send_notification(preference, previous_stat, new_stat)
    
    if not should_notify:
        return False

    emoji = "🔴" if is_down else "🟢"
    status = "offline" if is_down else "online"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji} Service Status Alert"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Service Name:*\n{service_name}"},
                {"type": "mrkdwn", "text": f"*Status:*\n{status.upper()}"},
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*URL:* <{service_url}|{service_url}>"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "Message delivered by: <https://pingmaster.fr/dashboard|PingMaster>"
                }
            ]
        }
    ]

    if preference.notification_method == NotificationMethod.SLACK:
        success = await send_slack_notification(preference.webhook_url, {"blocks": blocks})
        
        if success:
            preference.last_alert_time = datetime.utcnow()
            db_session.add(preference)
            db_session.commit()
            
        return success

    return False
