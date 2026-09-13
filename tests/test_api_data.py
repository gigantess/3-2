import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "data_count" in data

def test_data_crud_and_summary():
    # 1. Create a data item
    new_item = {
        "date": "2026-09-12",
        "value": 82500.0,
        "memo": "신규 테스트 데이터 - 외국인 대량 순매수"
    }
    create_res = client.post("/api/data", json=new_item)
    assert create_res.status_code == 201
    created_data = create_res.json()
    assert created_data["date"] == "2026-09-12"
    assert created_data["value"] == 82500.0
    doc_id = created_data["id"]

    # 2. Get single item
    get_res = client.get(f"/api/data/{doc_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == doc_id

    # 3. Update item
    update_data = {
        "value": 83000.0,
        "memo": "종가 상향 수정"
    }
    update_res = client.put(f"/api/data/{doc_id}", json=update_data)
    assert update_res.status_code == 200
    assert update_res.json()["value"] == 83000.0
    assert update_res.json()["memo"] == "종가 상향 수정"

    # 4. Get summary
    summary_res = client.get("/api/data/summary")
    assert summary_res.status_code == 200
    summary = summary_res.json()
    assert summary["count"] >= 1
    assert "period" in summary
    assert "metrics" in summary
    assert "trend" in summary
    assert summary["metrics"]["max"] >= 83000.0

    # 5. List items
    list_res = client.get("/api/data?limit=10&sort_order=desc")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert "items" in list_data
    assert "total" in list_data

    # 6. Export CSV
    export_csv = client.get("/api/data/export?format=csv")
    assert export_csv.status_code == 200
    assert "text/csv" in export_csv.headers["content-type"]
    assert "date,value,memo" in export_csv.text

    # 7. Export JSON
    export_json = client.get("/api/data/export?format=json")
    assert export_json.status_code == 200
    assert export_json.headers["content-type"] == "application/json"

    # 8. Delete item
    del_res = client.delete(f"/api/data/{doc_id}")
    assert del_res.status_code == 200

    # 9. Verify 404 after deletion
    get_del = client.get(f"/api/data/{doc_id}")
    assert get_del.status_code == 404

def test_data_validation_error():
    # Invalid date format
    bad_item = {
        "date": "2026/09/12",  # invalid
        "value": 80000.0,
        "memo": "bad date"
    }
    res = client.post("/api/data", json=bad_item)
    assert res.status_code == 422
