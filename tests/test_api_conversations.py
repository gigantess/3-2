import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_conversations_crud():
    # 1. Create conversation
    new_conv = {
        "title": "삼성전자 주가 분석 세션 1",
        "messages": [
            {"role": "user", "content": "삼성전자 최근 20일 추세는 어떤가요?"},
            {"role": "assistant", "content": "최근 20일 이동평균선 대비 보합 흐름을 보이고 있습니다."}
        ]
    }
    create_res = client.post("/api/conversations", json=new_conv)
    assert create_res.status_code == 201
    created = create_res.json()
    conv_id = created["id"]
    assert created["title"] == "삼성전자 주가 분석 세션 1"
    assert len(created["messages"]) == 2

    # 2. List conversations
    list_res = client.get("/api/conversations")
    assert list_res.status_code == 200
    conv_list = list_res.json()
    assert isinstance(conv_list, list)
    assert any(c["id"] == conv_id for c in conv_list)

    # 3. Get single conversation
    get_res = client.get(f"/api/conversations/{conv_id}")
    assert get_res.status_code == 200
    conv_detail = get_res.json()
    assert conv_detail["id"] == conv_id
    assert len(conv_detail["messages"]) == 2
    assert conv_detail["messages"][0]["content"] == "삼성전자 최근 20일 추세는 어떤가요?"

    # 4. Delete conversation
    del_res = client.delete(f"/api/conversations/{conv_id}")
    assert del_res.status_code == 200

    # 5. Verify 404 after delete
    get_del = client.get(f"/api/conversations/{conv_id}")
    assert get_del.status_code == 404
