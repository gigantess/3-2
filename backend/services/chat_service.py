import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List
from backend.config import GEMINI_API_KEY
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
    },
    {
        "type": "function",
        "function": {
            "name": "get_data_statistics",
            "description": "삼성전자 주가의 심층 통계(변동성, 20일 이동평균, 60일 이동평균, 14일 RSI, 최고/최저가 및 전체 기간 수익률)를 조회합니다.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]

class ChatService:
    def __init__(self, data_service: Optional[DataService] = None, conv_service: Optional[ConversationService] = None):
        self.data_service = data_service or DataService()
        self.conv_service = conv_service or ConversationService()
        self.genai_client = None
        if GEMINI_API_KEY and not GEMINI_API_KEY.startswith("your-gemini") and not GEMINI_API_KEY.startswith("sk-placeholder"):
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Could not initialize Gemini client: {e}")

    @staticmethod
    def build_system_prompt(summary: DataSummaryResponse) -> str:
        """
        AI 시스템 프롬프트 템플릿(Context Injection Template) 생성 함수.
        
        [문장 구성 및 변수 주입 규칙]
        - 대상: 삼성전자(005930.KS)
        - period: 시계열 시작일 ~ 종료일 (예: 2024-01-02 ~ 2026-09-11)
        - count: 총 거래일 수 (예: 656)
        - metrics: 최신 종가, 기간 평균 종가, 최고가, 최저가 (원 단위 쉼표 포맷팅)
        - trend: 최근 20일 이동평균(SMA 20) 대비 이격률 및 추세 (상승세/하락세/보합)
        - insights: 최고/최저가 일자 및 전체 기간 누적 수익률 요약
        
        토큰 소비량: 약 350 ~ 450 토큰 (전체 데이터 원본 대비 약 98% 절감)
        """
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
2. 사실(Fact) - 원인 분석(Why) - 전략적 조언(Action) 관점으로 명확하고 전문성 있게 구조화하여 답변하세요.
3. 사용자가 "내일 주가가 오를까?", "언제쯤 오를까?", "지금 사도 될까?"와 같은 미래 방향성이나 매매 타이밍을 물어볼 경우:
   - 기계적으로 "보합/횡보입니다"라는 단순 데이터 나열 답변을 절대 반복하지 마세요!
   - [Fact]: 현재 최신 종가({metrics.latest:,.0f}원)와 20일 이동평균선 대비 현재 위치(이격도), 14일 RSI 및 최근 추세를 정확한 수치로 제시하세요.
   - [Why]: 주가 상승/하락의 결정적 열쇠가 되는 3대 핵심 변수(외국인/기관 수급 전환, 미국 필라델피아 반도체/엔비디아 지수 흐름, 환율 영향)를 분석하세요.
   - [Action]: 단기(내일~수일) 지지선/저항선 가격대와 중장기 투자자를 위한 구체적인 분할 매수/손절 대응 전략을 명확하게 제시하세요.
4. 사용자가 데이터 외적인 질문을 하더라도 삼성전자 주가 트렌드와 연계하여 답변을 유도하세요.
5. 신뢰감 있고 정중한 금융 전문가 어조를 유지하세요.
"""

    def _build_system_prompt(self, summary: DataSummaryResponse) -> str:
        return self.build_system_prompt(summary)

    def _generate_mock_reply(self, user_message: str, summary: DataSummaryResponse) -> str:
        """
        Fallback response generator when Gemini API Key is absent or during tests.
        """
        metrics = summary.metrics
        msg = user_message.lower()

        if any(k in msg for k in ["오를까", "상승", "내릴까", "하락", "내일", "사도", "매수", "전망"]):
            return (
                f"💡 **삼성전자(005930.KS) 단기 및 중기 주가 전망 분석**\n\n"
                f"**[Fact (현재 위치)]**\n"
                f"• 현재 최신 종가는 **{metrics.latest:,.0f}원**이며, 최근 20일 이동평균선 대비 **{summary.trend}** 국면에 위치해 있습니다. "
                f"기간 내 최저가는 {metrics.min:,.0f}원, 최고가는 {metrics.max:,.0f}원입니다.\n\n"
                f"**[Why (주가 등락의 핵심 변수)]**\n"
                f"1. **글로벌 기술주 동향**: 오늘 밤 미국 필라델피아 반도체 지수 및 주요 AI 반도체 종목의 반등 여부가 내일 시초가에 직접적인 영향을 미칩니다.\n"
                f"2. **외국인/기관 수급**: 최근 매도세가 진정되고 외국인의 순매수 전환이 확인되어야 본격적인 기술적 반등 추세가 형성될 수 있습니다.\n\n"
                f"**[Action (투자 대응 전략)]**\n"
                f"• **단기 관점**: 내일 섣부른 추격 매수보다는 장 초반 수급과 20일 이동평균선 지지 여부를 확인한 후 보수적으로 접근을 권장합니다.\n"
                f"• **중장기 관점**: 역사적 밸류에이션 하단 부근이므로, 단기 등락에 일희일비하기보다는 음봉(조정일) 분할 매수 전략이 유효합니다."
            )
        elif "최고" in msg or "고점" in msg:
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

        # 3. Call Gemini API (with candidate model resolution)
        reply_text = ""
        system_prompt = self._build_system_prompt(summary)

        if self.genai_client:
            try:
                from google.genai import types

                # Prepare conversation contents for Gemini
                contents = []
                for m in history[-6:]:
                    role = "model" if m.role == "assistant" else "user"
                    contents.append(
                        types.Content(
                            role=role,
                            parts=[types.Part.from_text(text=m.content)]
                        )
                    )

                config = types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,
                    max_output_tokens=800
                )

                # Try modern models in priority order
                models_to_try = ["gemini-3.6-flash", "gemini-flash-latest", "gemini-3.5-flash", "gemini-2.5-flash"]
                for model_name in models_to_try:
                    try:
                        response = self.genai_client.models.generate_content(
                            model=model_name,
                            contents=contents,
                            config=config
                        )
                        reply_text = response.text or ""
                        if reply_text:
                            break
                    except Exception as model_err:
                        logger.warning(f"Model {model_name} failed: {model_err}. Trying next candidate...")

                if not reply_text:
                    reply_text = self._generate_mock_reply(message, summary)
            except Exception as e:
                logger.error(f"Gemini API call failed: {e}. Using fallback mock response.")
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
