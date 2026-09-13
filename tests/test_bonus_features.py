import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_statistics_endpoint_bonus():
    """
    Test the bonus /api/data/statistics endpoint which provides extended quantitative metrics
    such as volatility (standard deviation), 20-day SMA, 60-day SMA, RSI momentum, and return rate.
    """
    response = client.get("/api/data/statistics")
    assert response.status_code == 200
    data = response.json()

    # Core statistical fields
    assert "period" in data
    assert "count" in data
    assert data["count"] > 0
    assert "volatility" in data
    assert "sma_20" in data
    assert "sma_60" in data
    assert "max_price" in data
    assert "max_date" in data
    assert "min_price" in data
    assert "min_date" in data
    assert "total_return_pct" in data
    assert "rsi_14" in data

    # Numerical assertions
    assert isinstance(data["volatility"], (int, float))
    assert isinstance(data["sma_20"], (int, float))
    assert isinstance(data["rsi_14"], (int, float))
    assert 0 <= data["rsi_14"] <= 100

def test_mcp_tools_definition_bonus():
    """
    Test that Model Context Protocol (MCP) / Function Calling tools are defined and callable.
    """
    from backend.services.chat_service import TOOLS
    tool_names = [t["function"]["name"] for t in TOOLS]
    assert "get_data_summary" in tool_names
    assert "get_data_statistics" in tool_names
