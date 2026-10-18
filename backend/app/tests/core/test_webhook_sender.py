import logging
import pytest
from unittest.mock import AsyncMock, Mock, patch

from app.core.notifications import send_slack_notification


@pytest.mark.asyncio
async def test_send_slack_notification_posts_to_public_webhook():
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_post.return_value = Mock(status_code=200)
        assert await send_slack_notification("https://hooks.slack.com/services/T/B/X", "hello") is True
        mock_post.assert_called_once()


@pytest.mark.asyncio
async def test_send_slack_notification_skips_private_webhook(fake_dns, caplog):
    fake_dns["hooks.internal.example"] = ["169.254.169.254"]
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post, \
         caplog.at_level(logging.WARNING, logger="app.core.notifications"):
        assert await send_slack_notification("https://hooks.internal.example/x", "hello") is False
        mock_post.assert_not_called()
    assert any(r.levelno == logging.WARNING for r in caplog.records)


@pytest.mark.asyncio
async def test_send_slack_notification_skips_non_http_scheme():
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        assert await send_slack_notification("file:///etc/passwd", "hello") is False
        mock_post.assert_not_called()


@pytest.mark.asyncio
async def test_send_slack_notification_does_not_follow_redirects():
    with patch('app.core.notifications.httpx.AsyncClient') as mock_client_cls:
        client = mock_client_cls.return_value.__aenter__.return_value
        client.post = AsyncMock(return_value=Mock(status_code=200))
        await send_slack_notification("https://hooks.slack.com/services/T/B/X", "hello")
    assert mock_client_cls.call_args.kwargs["follow_redirects"] is False
