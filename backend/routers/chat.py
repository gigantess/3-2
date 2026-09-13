from fastapi import APIRouter
from backend.schemas.chat import ChatRequest, ChatResponse
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])
chat_service = ChatService()

@router.post("", response_model=ChatResponse, summary="AI 대화 (컨텍스트 주입 + 자동 대화 저장)")
async def chat_with_ai(request: ChatRequest):
    """
    1. 데이터 요약 조회 (/api/data/summary)
    2. 요약을 시스템 프롬프트에 자동 주입
    3. GPT API 호출 (OpenAI / Mock fallback)
    4. 대화 내용을 conversations 컬렉션에 자동 저장
    """
    return await chat_service.chat(
        message=request.message,
        conversation_id=request.conversation_id
    )
