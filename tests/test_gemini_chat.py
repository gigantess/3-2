import pytest
from unittest.mock import MagicMock
from backend.services.chat_service import ChatService

@pytest.mark.anyio
async def test_chat_service_with_gemini_client():
    cs = ChatService()
    mock_genai_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '안녕하세요! Gemini가 분석한 결과입니다.'
    mock_genai_client.models.generate_content.return_value = mock_response
    cs.genai_client = mock_genai_client

    resp = await cs.chat('삼성전자 요약해줘')
    assert resp.reply == '안녕하세요! Gemini가 분석한 결과입니다.'
    assert mock_genai_client.models.generate_content.called

@pytest.mark.anyio
async def test_chat_service_fallback_when_no_client():
    cs = ChatService()
    cs.genai_client = None

    resp = await cs.chat('삼성전자 최고가가 얼마야?')
    assert '최고가' in resp.reply
    assert resp.summary_used is not None
