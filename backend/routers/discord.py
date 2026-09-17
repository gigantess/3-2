import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from backend.services.chat_service import ChatService
from backend.services.data_service import DataService
from backend.services.discord_service import DiscordService
from backend.schemas.chat import ChatRequest, ChatResponse

logger = logging.getLogger("backend.routers.discord")

router = APIRouter(prefix="/api/discord", tags=["Discord"])
chat_service = ChatService()
data_service = DataService()
discord_service = DiscordService()

class DiscordChatResponse(ChatResponse):
    sent_to_discord: bool = Field(True, description="Discord 채널 전송 성공 여부")

@router.get("/status", summary="Discord 웹후크 연동 상태 조회")
def get_discord_status():
    """
    Discord 웹후크 URL 설정 여부 및 상태를 확인합니다.
    """
    return {
        "configured": discord_service.is_configured(),
        "channel_type": "Discord Webhook",
        "description": "실시간 AI 채팅 답변 및 시장 브리핑 전송 활성화"
    }

@router.post("/chat", response_model=DiscordChatResponse, summary="AI 채팅 질의 및 Discord 동시 전송")
async def chat_with_discord_broadcast(chat_in: ChatRequest, background_tasks: BackgroundTasks):
    """
    사용자의 질문을 수신하여 AI 컨텍스트 주입 답변을 생성하고,
    동시에 Discord 웹후크 채널로 리치 임베드(Embed) 브리핑을 실시간 발송합니다.
    """
    try:
        # 1. Run AI Chat with Context Injection
        response = await chat_service.chat(
            message=chat_in.message,
            conversation_id=chat_in.conversation_id
        )

        # 2. Send to Discord
        sent = False
        if discord_service.is_configured():
            sent = discord_service.send_chat_message(
                user_message=chat_in.message,
                ai_reply=response.reply,
                summary=response.summary_used
            )

        return DiscordChatResponse(
            conversation_id=response.conversation_id,
            reply=response.reply,
            summary_used=response.summary_used,
            sent_to_discord=sent
        )
    except Exception as e:
        logger.error(f"Error in discord chat broadcast: {e}")
        raise HTTPException(status_code=500, detail=f"Discord 연동 채팅 실패: {str(e)}")

@router.post("/briefing", summary="삼성전자 주가 분석 브리핑을 Discord 채널로 즉시 전송")
def send_discord_market_briefing():
    """
    현재 시계열 주가 요약(기간, 건수, 최신가, 20일 추세)과
    보조지표(RSI 14, 20일 변동성, 매매 신호)를 Discord 채널로 발송합니다.
    """
    if not discord_service.is_configured():
        raise HTTPException(status_code=400, detail="Discord 웹후크 URL이 설정되어 있지 않습니다.")

    summary = data_service.get_summary()
    stats = data_service.get_statistics()

    success = discord_service.send_market_briefing(summary=summary, stats=stats)
    if not success:
        raise HTTPException(status_code=500, detail="Discord 브리핑 전송에 실패했습니다.")

    return {
        "status": "success",
        "message": "삼성전자 주가 분석 리포트가 Discord 채널로 성공적으로 발송되었습니다.",
        "period": summary.period,
        "latest_price": summary.metrics.latest,
        "trend": summary.trend
    }
