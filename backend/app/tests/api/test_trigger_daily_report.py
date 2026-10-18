from unittest.mock import AsyncMock, patch


def test_trigger_daily_report_requires_auth(client):
    response = client.post("/api/trigger-daily-report")
    assert response.status_code == 401


def test_trigger_daily_report_runs_report_for_authenticated_user(client, auth_headers):
    with patch("app.main.generate_daily_report", new_callable=AsyncMock) as report:
        response = client.post("/api/trigger-daily-report", headers=auth_headers)
    assert response.status_code == 200
    report.assert_awaited_once()
