from typing import List
from fastapi import APIRouter, HTTPException
from backend.schemas.conversation import (
    ConversationCreate,
    ConversationResponse,
    ConversationListItem
)
from backend.services.conversation_service import ConversationService

router = APIRouter(prefix="/api/conversations", tags=["Conversations"])
conv_service = ConversationService()

@router.post("", response_model=ConversationResponse, status_code=201, summary="대화 저장")
def create_conversation(conv: ConversationCreate):
    """
    새로운 대화 세션 및 메시지 목록을 저장합니다.
    """
    return conv_service.create_conversation(conv)

@router.get("", response_model=List[ConversationListItem], summary="대화 목록 조회")
def get_conversations():
    """
    저장된 이전 대화 목록(제목, 마지막 메시지, 메시지 수 등)을 최신순으로 조회합니다.
    """
    return conv_service.list_conversations()

@router.get("/{id}", response_model=ConversationResponse, summary="특정 대화 전체 메시지 조회")
def get_conversation(id: str):
    """
    대화 불러오기 UX를 위해 특정 대화의 전체 메시지 내역을 조회합니다.
    """
    conv = conv_service.get_conversation(id)
    if not conv:
        raise HTTPException(status_code=404, detail="해당 ID의 대화를 찾을 수 없습니다.")
    return conv

@router.delete("/{id}", summary="대화 삭제")
def delete_conversation(id: str):
    """
    지정한 대화 세션을 삭제합니다.
    """
    success = conv_service.delete_conversation(id)
    if not success:
        raise HTTPException(status_code=404, detail="해당 ID의 대화를 찾을 수 없습니다.")
    return {"message": "대화가 성공적으로 삭제되었습니다.", "id": id}
