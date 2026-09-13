import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_chat_api_context_injection():
    # 1. Ask a question without conversation_id (should create new session)
    chat_payload = {
        "message": "삼성전자의 현재까지 최고가와 최저가가 얼마인지 알려줘"
    }
    res = client.post("/api/chat", json=chat_payload)
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    assert "reply" in data
    assert len(data["reply"]) > 0
    assert "summary_used" in data
    assert data["summary_used"]["count"] > 0
    conv_id = data["conversation_id"]

    # 2. Continue the conversation with conversation_id
    followup_payload = {
        "message": "최근 20거래일 흐름은 어때?",
        "conversation_id": conv_id
    }
    res2 = client.post("/api/chat", json=followup_payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["conversation_id"] == conv_id
    assert len(data2["reply"]) > 0

    # 3. Verify conversation was saved automatically in /api/conversations/{id}
    conv_res = client.get(f"/api/conversations/{conv_id}")
    assert conv_res.status_code == 200
    conv_data = conv_res.json()
    # Should have 4 messages: user 1, assistant 1, user 2, assistant 2
    assert len(conv_data["messages"]) == 4
    assert conv_data["messages"][0]["role"] == "user"
    assert conv_data["messages"][1]["role"] == "assistant"
    assert conv_data["messages"][2]["role"] == "user"
    assert conv_data["messages"][3]["role"] == "assistant"
