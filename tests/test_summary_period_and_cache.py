import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.data_service import DataService
from backend.services.conversation_service import ConversationService
from backend.services.chat_service import ChatService
from backend.schemas.data import DataSummaryResponse, DataMetrics

client = TestClient(app)

def test_summary_period_filtering():
    """Test period filtering (start_date, end_date) on /api/data/summary endpoint."""
    # Ensure test items exist
    item1 = {"date": "2024-05-10", "value": 75000.0, "memo": "5월 데이터"}
    item2 = {"date": "2025-05-10", "value": 85000.0, "memo": "다음해 5월 데이터"}
    client.post("/api/data", json=item1)
    client.post("/api/data", json=item2)

    # Filter for 2024 only
    res_2024 = client.get("/api/data/summary?start_date=2024-01-01&end_date=2024-12-31")
    assert res_2024.status_code == 200
    data_2024 = res_2024.json()
    assert "2024" in data_2024["period"]
    assert data_2024["count"] >= 1

    # Filter for non-existent future date
    res_future = client.get("/api/data/summary?start_date=2099-01-01&end_date=2099-12-31")
    assert res_future.status_code == 200
    data_future = res_future.json()
    assert data_future["count"] == 0
    assert "데이터 없음" in data_future["period"]

def test_summary_caching_and_invalidation():
    """Test that summary is cached and properly invalidated upon data mutations."""
    ds = DataService()
    
    # Initial summary
    s1 = ds.get_summary()
    assert s1 is not None

    # Call again immediately (should be served from cache)
    s2 = ds.get_summary()
    assert s1.metrics.latest == s2.metrics.latest

    # Mutate data by adding a new item with a future date
    from backend.schemas.data import DataItemCreate
    new_doc = ds.add_item(DataItemCreate(date="2099-12-31", value=99999.0, memo="캐시 무효화 테스트용"))

    # Summary should be refreshed and cache invalidated
    s3 = ds.get_summary()
    assert s3.metrics.latest == 99999.0

    # Cleanup
    ds.delete_item(new_doc.id)
    s4 = ds.get_summary()
    assert s4.metrics.latest != 99999.0

def test_input_validation_and_sanitization():
    """Test 422 errors and XSS sanitization."""
    # Negative price -> 422 error
    res_neg = client.post("/api/data", json={"date": "2026-09-15", "value": -500.0, "memo": "음수"})
    assert res_neg.status_code == 422

    # Price exceeding 10,000,000 -> 422 error
    res_huge = client.post("/api/data", json={"date": "2026-09-15", "value": 99999999.0, "memo": "초과가"})
    assert res_huge.status_code == 422

    # Invalid date pattern
    res_date = client.post("/api/data", json={"date": "2026/09/15", "value": 70000.0})
    assert res_date.status_code == 422

    # XSS Script tag stripping in memo
    xss_item = {"date": "2026-09-15", "value": 77000.0, "memo": "<script>alert('xss')</script>보안 테스트"}
    res_xss = client.post("/api/data", json=xss_item)
    assert res_xss.status_code == 201
    created = res_xss.json()
    assert "<script>" not in created["memo"]
    assert "alert" not in created["memo"]

    # Cleanup
    client.delete(f"/api/data/{created['id']}")

def test_conversation_policies():
    """Test message length limit and conversation message handling."""
    conv_svc = ConversationService()
    conv_id = "test-policy-conv"
    
    # Message exceeding 4000 characters
    long_text = "삼성전자 주가 분석 " * 350 # ~3500-4500 chars
    res = conv_svc.add_message(conv_id, "user", long_text)
    assert len(res.messages) == 1
    assert len(res.messages[0].content) <= 4100
    if len(long_text) > 4000:
        assert "생략" in res.messages[0].content

    # Cleanup
    conv_svc.delete_conversation(conv_id)

def test_system_prompt_builder():
    """Test build_system_prompt output format and contents."""
    summary = DataSummaryResponse(
        period="2024-01-02 ~ 2026-09-11",
        count=656,
        metrics=DataMetrics(total=45000000.0, average=75000.0, max=88000.0, min=62000.0, latest=81000.0),
        trend="상승세 (+3.5%)",
        insights="전체 기간 최고가는 88,000원입니다."
    )
    prompt = ChatService.build_system_prompt(summary)
    assert "삼성전자(005930.KS)" in prompt
    assert "2024-01-02 ~ 2026-09-11" in prompt
    assert "81,000원" in prompt
    assert "88,000원" in prompt
    assert "상승세 (+3.5%)" in prompt
