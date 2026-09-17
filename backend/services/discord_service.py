import json
import logging
import urllib.request
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from backend.config import DISCORD_WEBHOOK_URL
from backend.schemas.data import DataSummaryResponse

logger = logging.getLogger("backend.discord_service")

class DiscordService:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or DISCORD_WEBHOOK_URL

    def is_configured(self) -> bool:
        return bool(self.webhook_url and self.webhook_url.startswith("https://discord.com/api/webhooks/"))

    def _post_payload(self, payload: Dict[str, Any]) -> bool:
        if not self.is_configured():
            logger.warning("Discord webhook URL is not configured.")
            return False

        try:
            data_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=data_bytes,
                headers={
                    "Content-Type": "application/json; charset=utf-8",
                    "User-Agent": "SamsungStockAI-Assistant/1.0"
                }
            )
            with urllib.request.urlopen(req, timeout=10) as res:
                if res.status in (200, 204):
                    return True
                logger.warning(f"Discord webhook responded with status {res.status}")
                return False
        except Exception as e:
            logger.error(f"Failed to post to Discord webhook: {e}")
            return False

    def send_chat_message(
        self,
        user_message: str,
        ai_reply: str,
        summary: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Sends user question and AI analytical reply to Discord channel as an interactive Embed.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        
        # Color coding by trend
        color = 0x3b82f6 # Blue default
        trend_str = "보합 / 분석 중"
        if summary:
            trend_str = summary.get("trend", "")
            if "상승" in trend_str:
                color = 0x10b981 # Green
            elif "하락" in trend_str:
                color = 0xf43f5e # Red

        # Format AI reply safely for Discord field limits (max 1024 chars per field)
        clean_reply = ai_reply
        if len(clean_reply) > 1000:
            clean_reply = clean_reply[:990] + "...\n*(전체 내용은 웹 화면 참조)*"

        fields = [
            {
                "name": "❓ 사용자 질문",
                "value": user_message[:500] if user_message else "내용 없음",
                "inline": False
            },
            {
                "name": "💡 AI 분석 조언 (Fact • Why • Action)",
                "value": clean_reply,
                "inline": False
            }
        ]

        if summary and "metrics" in summary:
            m = summary["metrics"]
            fields.append({
                "name": "📊 실시간 데이터 컨텍스트",
                "value": (
                    f"• **최신 종가**: {m.get('latest', 0):,.0f}원\n"
                    f"• **20일 추세**: {trend_str}\n"
                    f"• **기간 평균**: {m.get('average', 0):,.0f}원 (최고 {m.get('max', 0):,.0f}원 / 최저 {m.get('min', 0):,.0f}원)"
                ),
                "inline": False
            })

        embed = {
            "title": "🤖 삼성전자(005930.KS) AI 비서 대화 브리핑",
            "color": color,
            "fields": fields,
            "footer": {
                "text": "Samsung Stock AI Assistant (3-2) • Gemini 2.5 Flash",
                "icon_url": "https://img.icons8.com/color/48/artificial-intelligence.png"
            },
            "timestamp": now_iso
        }

        payload = {
            "username": "삼성전자 AI 비서",
            "avatar_url": "https://img.icons8.com/fluency/96/bullish.png",
            "embeds": [embed]
        }

        return self._post_payload(payload)

    def send_market_briefing(self, summary: DataSummaryResponse, stats: Optional[Dict[str, Any]] = None) -> bool:
        """
        Sends comprehensive daily market briefing & technical signals to Discord.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        m = summary.metrics

        rsi_text = f"{stats.get('rsi_14', 50.0):.1f}" if stats else "-"
        volatility_text = f"{stats.get('volatility', 0.0):,.0f}원" if stats else "-"
        sma20_text = f"{stats.get('sma_20', 0.0):,.0f}원" if stats else "-"

        # Determine signal badge text
        signal_badge = "🟡 중립 / 관망"
        if stats:
            rsi = stats.get("rsi_14", 50.0)
            if rsi >= 70:
                signal_badge = "🔴 과열 / 분할 매도 고려 (RSI 과매수)"
            elif rsi <= 30:
                signal_badge = "🟢 과매도 / 분할 매수 기회 (RSI 과매도)"
            elif "상승" in summary.trend:
                signal_badge = "🟢 추세 상승 / 보유 및 추종"
            elif "하락" in summary.trend:
                signal_badge = "🔴 단기 조정 / 비중 축소"

        fields = [
            {
                "name": "📈 주가 핵심 지표",
                "value": (
                    f"• **최신 종가**: **{m.latest:,.0f}원**\n"
                    f"• **분석 기간**: {summary.period} ({summary.count}개 거래일)\n"
                    f"• **평균 가격**: {m.average:,.0f}원\n"
                    f"• **가격 범위**: {m.min:,.0f}원 ~ {m.max:,.0f}원"
                ),
                "inline": True
            },
            {
                "name": "⚡ 기술적 지표 & 신호",
                "value": (
                    f"• **매매 신호**: {signal_badge}\n"
                    f"• **14일 RSI**: `{rsi_text}`\n"
                    f"• **20일 이동평균**: {sma20_text}\n"
                    f"• **20일 변동성**: {volatility_text}"
                ),
                "inline": True
            },
            {
                "name": "📌 3-1 핵심 인사이트 & 전략 제언",
                "value": f"{summary.insights or '특이사항 없음'}\n\n💡 **추세 진단**: {summary.trend}",
                "inline": False
            }
        ]

        embed = {
            "title": "🔔 [정기 브리핑] 삼성전자(005930.KS) 주가 시계열 & 기술적 분석",
            "description": "3-1 시계열 데이터셋 및 20일 이동평균선(SMA 20) 추세 알고리즘 기반 분석 보고서입니다.",
            "color": 0x3b82f6 if "상승" not in summary.trend else 0x10b981,
            "fields": fields,
            "footer": {
                "text": "Samsung Stock AI Assistant (3-2) • Automated Briefing",
                "icon_url": "https://img.icons8.com/color/48/bullish.png"
            },
            "timestamp": now_iso
        }

        payload = {
            "username": "삼성전자 AI 비서",
            "avatar_url": "https://img.icons8.com/fluency/96/bullish.png",
            "embeds": [embed]
        }

        return self._post_payload(payload)
