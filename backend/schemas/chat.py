from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., description="사용자 질문 또는 지시어", examples=["현재까지 평균 주가와 최근 흐름을 알려줘"])
    conversation_id: Optional[str] = Field(None, description="기존 대화 이어하기 위한 세션 ID")

class ChatResponse(BaseModel):
    conversation_id: str = Field(..., description="대화 세션 ID")
    reply: str = Field(..., description="AI 답변 본문")
    summary_used: Optional[Dict[str, Any]] = Field(None, description="프롬프트 주입에 사용된 데이터 요약 스냅샷")
