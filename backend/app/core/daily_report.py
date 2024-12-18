from datetime import datetime, timedelta
import logging
import os
from sqlalchemy import func
from app.db.session import SessionLocal
from app.db.models import User, Service, ServiceStats
from app.core.notifications import send_slack_notification

logger = logging.getLogger(__name__)

def get_daily_stats():
    """Collect daily statistics from the database"""
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        
        # Get new users with their names
        new_users = db.query(User).filter(User.created_at >= yesterday).all()
        new_users_list = [f"• {user.username}" for user in new_users]  # Assuming User has a 'name' field
        
        stats = {
            "total_users": db.query(User).count(),
            "new_users_24h": len(new_users),
            "new_users_list": new_users_list,  # Add new users list to stats
            "total_services": db.query(Service).count(),
            "new_services_24h": db.query(Service).filter(Service.created_at >= yesterday).count(),
            "total_pings": db.query(ServiceStats).count(),
            "pings_24h": db.query(ServiceStats).filter(ServiceStats.ping_date >= yesterday).count(),
        }
        
        return stats
    finally:
        db.close()

def format_slack_message(stats):
    """Format statistics into a Slack message"""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Rapport quotidien PingMaster"
            }
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Utilisateurs total:*\n{stats['total_users']}"},
                {"type": "mrkdwn", "text": f"*Nouveaux utilisateurs (24h):*\n{stats['new_users_24h']}"},
                {"type": "mrkdwn", "text": f"*Services total:*\n{stats['total_services']}"},
                {"type": "mrkdwn", "text": f"*Nouveaux services (24h):*\n{stats['new_services_24h']}"},
                {"type": "mrkdwn", "text": f"*Pings total:*\n{stats['total_pings']}"},
                {"type": "mrkdwn", "text": f"*Pings (24h):*\n{stats['pings_24h']}"}
            ]
        }
    ]

    # Add new users section if there are any new users
    if stats['new_users_list']:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Nouveaux utilisateurs:*\n" + "\n".join(stats['new_users_list'])
            }
        })

    return {"blocks": blocks}

async def generate_daily_report():
    """Generate and send daily report to Slack"""
    try:
        sentry_webhook_url = os.getenv("SENTRY_WEBHOOK_URL_MONITORING")
        stats = get_daily_stats()
        message = format_slack_message(stats)
        await send_slack_notification(sentry_webhook_url, message)
        logger.info("Daily report sent successfully")
    except Exception as e:
        logger.error(f"Error generating daily report: {str(e)}")