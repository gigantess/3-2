import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.discord_service import DiscordService

client = TestClient(app)

def test_discord_status():
    res = client.get("/api/discord/status")
    assert res.status_code == 200
    data = res.json()
    assert data["configured"] is True
    assert "Discord Webhook" in data["channel_type"]

def test_discord_service_unit():
    svc = DiscordService()
    assert svc.is_configured() is True
    
    # Test sending chat embed
    sent = svc.send_chat_message(
        user_message="삼성전자 2026년 주가 전망 및 트렌드는 어때?",
        ai_reply="분석 데이터 기준 삼성전자는 20일 이동평균선 상향 돌파 후 견조한 흐름을 유지하고 있습니다.",
        summary={
            "period": "2024-01-02 ~ 2026-09-11",
            "trend": "상승세 (+3.2%)",
            "metrics": {"latest": 81000.0, "average": 75000.0, "max": 88800.0, "min": 62300.0}
        }
    )
    assert sent is True

def test_discord_chat_endpoint():
    res = client.post("/api/discord/chat", json={
        "message": "테스트 자동화: 최신 종가 및 트렌드 요약 부탁해"
    })
    assert res.status_code == 200
    data = res.json()
    assert "reply" in data
    assert data["sent_to_discord"] is True

def test_discord_briefing_endpoint():
    res = client.post("/api/discord/briefing")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "발송되었습니다" in data["message"]
