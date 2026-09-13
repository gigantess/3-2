import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from backend.config import OPENAI_API_KEY
from backend.services.data_service import DataService
from backend.services.conversation_service import ConversationService
from backend.schemas.chat import ChatResponse
from backend.schemas.data import DataSummaryResponse

logger = logging.getLogger("backend.chat_service")

# OpenAI Function Calling Tools Definition (Bonus requirement)
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_data_summary",
            "description": "삼성전자 주가 시계열 데이터의 전체 요약 통계(기간, 건수, 평균/최고/최저/최신가, 최근 추세)를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_recent_data_items",
            "description": "최근 N개의 일별 주가 기록(날짜, 종가, 메모)을 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "조회할 최근 거래일 수 (기본 5개)",
                        "default": 5
                    }
                }
            }
        }
    }
]

class ChatService:
    def __init__(self, data_service: Optional[DataService] = None, conv_service: Optional[ConversationService] = None):
        self.data_service = data_service or DataService()
        self.conv_service = conv_service or ConversationService()
        self.openai_client = None
        if OPENAI_API_KEY and not OPENAI_API_KEY.startswith("sk-placeholder"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")

    def _build_system_prompt(self, summary: DataSummaryResponse) -> str:
        metrics = summary.metrics
        return f"""당신은 삼성전자(005930.KS) 주가 시계열 데이터 분석 전문 AI 비서입니다.
사용자의 시계열 분석 데이터를 바탕으로 신뢰성 높고 친절한 금융/데이터 분석 맞춤형 답변을 제공하세요.

[사용자 데이터 요약]
- 분석 대상: 삼성전자(005930.KS) 일별 주가 시계열 데이터
- 데이터 기간: {summary.period}
- 총 레코드: {summary.count}개 거래일
- 주요 지표:
  * 최신 종가: {metrics.latest:,.0f}원
  * 평균 종가: {metrics.average:,.0f}원
  * 최고가: {metrics.max:,.0f}원
  * 최저가: {metrics.min:,.0f}원
- 최근 트렌드: {summary.trend}
- 심층 인사이트: {summary.insights or '특이사항 없음'}

[답변 가이드라인]
1. 반드시 위 요약 데이터를 기반으로 구체적인 수치(원 단위 쉼표 표기)를 들어 설명하세요.
2. 사실(Fact) - 원인 분석(Why) - 전략적 조언(Action) 관점으로 구조화하여 답변하세요.
3. 사용자가 데이터 외적인 질문을 하더라도 삼성전자 주가 트렌드와 연계하여 답변을 유도하세요.
4. 존댓말과 정중한 어조를 유지하세요.
"""

    def _generate_mock_reply(self, user_message: str, summary: DataSummaryResponse) -> str:
        """
        Fallback response generator when OpenAI API Key is absent or during tests.
        """
        metrics = summary.metrics
        msg = user_message.lower()

        if "최고" in msg or "고점" in msg:
            return (
                f"삼성전자 분석 데이터 기준 최고가는 **{metrics.max:,.0f}원**입니다. "
                f"전체 기간({summary.period}) 동안의 평균가({metrics.average:,.0f}원) 대비 높은 수준을 기록했던 핵심 저항선입니다."
            )
        elif "최저" in msg or "바닥" in msg or "저점" in msg:
            return (
                f"분석 데이터 기준 최저가는 **{metrics.min:,.0f}원**입니다. "
                f"해당 가격대는 과거 주요 지지선 역할을 하였으며, 현재 최신 종가({metrics.latest:,.0f}원)와 비교해 리스크 관리 기준점으로 활용할 수 있습니다."
            )
        elif "추세" in msg or "트렌드" in msg or "흐름" in msg or "어때" in msg:
            return (
                f"현재 삼성전자 주가 트렌드는 **{summary.trend}** 상태입니다.\n\n"
                f"• 최신 종가: **{metrics.latest:,.0f}원**\n"
                f"• 전체 평균: {metrics.average:,.0f}원\n"
                f"• 데이터 분석 기간: {summary.period} (총 {summary.count}개 거래일)\n\n"
                f"💡 **분석 조언**: {summary.insights}"
            )
        elif "평균" in msg or "실적" in msg or "요약" in msg:
            return (
                f"삼성전자 시계열 데이터 요약 보고입니다:\n\n"
                f"1. **데이터 기간**: {summary.period} (총 {summary.count}개 거래일)\n"
                f"2. **평균 가격**: {metrics.average:,.0f}원\n"
                f"3. **가격 범위**: 최저 {metrics.min:,.0f}원 ~ 최고 {metrics.max:,.0f}원\n"
                f"4. **최근 동향**: {summary.trend}\n\n"
                f"추가로 궁금하신 기간이나 세부 지표가 있으시면 편하게 질문해주세요!"
            )
        else:
            return (
                f"현재 보유하신 삼성전자 데이터({summary.period}, 총 {summary.count}건)를 분석한 결과, "
                f"최신 종가는 **{metrics.latest:,.0f}원**이며 전반적인 흐름은 **{summary.trend}**입니다. "
                f"평균 종가는 {metrics.average:,.0f}원선에 형성되어 있습니다. 구체적인 통계나 가격 전략에 대해 언제든 물어보세요!"
            )

    async def chat(self, message: str, conversation_id: Optional[str] = None) -> ChatResponse:
        # 1. Fetch current data summary
        summary = self.data_service.get_summary()

        # 2. Setup conversation session
        conv_id = conversation_id or str(uuid.uuid4())
        
        # Add user message to conversation history
        self.conv_service.add_message(conv_id, "user", message)

        # Retrieve conversation history
        conv = self.conv_service.get_conversation(conv_id)
        history = conv.messages if conv else []

        # 3. Call GPT API (or Mock if no key)
        reply_text = ""
        system_prompt = self._build_system_prompt(summary)

        if self.openai_client:
            try:
                # Prepare OpenAI messages
                messages = [{"role": "system", "content": system_prompt}]
                
                # Append last 6 messages for context
                for m in history[-6:]:
                    messages.append({"role": m.role, "content": m.content})

                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    temperature=0.7,
                    max_tokens=800
                )
                reply_text = response.choices[0].message.content or ""
            except Exception as e:
                logger.error(f"OpenAI API call failed: {e}. Using fallback mock response.")
                reply_text = self._generate_mock_reply(message, summary)
        else:
            reply_text = self._generate_mock_reply(message, summary)

        # 4. Save assistant reply to conversation
        self.conv_service.add_message(conv_id, "assistant", reply_text)

        return ChatResponse(
            conversation_id=conv_id,
            reply=reply_text,
            summary_used=summary.model_dump()
        )
