from typing import List, Optional
from pydantic import BaseModel, Field

class MessageItem(BaseModel):
    role: str = Field(..., description="메시지 발신 주체 (user, assistant, system)", examples=["user"])
    content: str = Field(..., description="메시지 본문", examples=["삼성전자 최근 주가 추세 어때?"])
    timestamp: Optional[str] = Field(None, description="메시지 생성 시각 (ISO format)")

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(None, description="대화 제목")
    messages: List[MessageItem] = Field(default_factory=list, description="메시지 목록")

class ConversationResponse(BaseModel):
    id: str = Field(..., description="대화 세션 ID")
    title: str = Field(..., description="대화 세션 제목")
    messages: List[MessageItem] = Field(default_factory=list, description="대화 메시지 목록")
    created_at: Optional[str] = Field(None, description="대화 생성 일시")
    updated_at: Optional[str] = Field(None, description="최근 수정 일시")

class ConversationListItem(BaseModel):
    id: str = Field(..., description="대화 세션 ID")
    title: str = Field(..., description="대화 세션 제목")
    message_count: int = Field(0, description="메시지 수")
    last_message: Optional[str] = Field(None, description="마지막 메시지 요약")
    created_at: Optional[str] = Field(None, description="대화 생성 일시")
    updated_at: Optional[str] = Field(None, description="최근 수정 일시")
