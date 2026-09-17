import sys
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

import discord
from backend.config import DISCORD_BOT_TOKEN
from backend.services.chat_service import ChatService
from backend.services.data_service import DataService

logger = logging.getLogger("backend.discord_bot")

class SamsungStockDiscordBot(discord.Client):
    def __init__(self, with_message_content: bool = True, *args, **kwargs):
        intents = discord.Intents.default()
        intents.messages = True
        if with_message_content:
            intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)
        self.with_message_content = with_message_content
        self.chat_service = ChatService()
        self.data_service = DataService()

    async def on_ready(self):
        logger.info(f"[Discord Bot] Logged in as {self.user} (ID: {self.user.id})")
        print(f"[Discord Bot] 양방향 AI 비서 봇 연결 완료: {self.user} (상태: 온라인)")
        print(f"[Discord Bot] -> 대화 방법: '!질문 내용' 또는 '@{self.user.name} 내용' 또는 '삼성전자 주가 어때?'")
        try:
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name="삼성전자 주가 | !질문 or 멘션"
                )
            )
        except Exception as e:
            logger.warning(f"Failed to set Discord presence: {e}")

    async def on_message(self, message: discord.Message):
        # Ignore messages sent by the bot itself or other bots
        if message.author.bot or message.author == self.user:
            return

        content = message.content.strip()
        is_mentioned = self.user in message.mentions
        is_dm = isinstance(message.channel, discord.DMChannel)

        print(f"[Discord Bot 수신] 작성자: {message.author} | 내용: '{content}' | 멘션여부: {is_mentioned}")

        # Check commands (flexible triggers)
        is_briefing_cmd = any(content.startswith(x) for x in ["!브리핑", "/브리핑", "브리핑", "!요약", "요약"])
        is_chat_cmd = (
            is_mentioned or is_dm or
            any(content.startswith(x) for x in ["!질문", "!삼성", "!주가", "!ask", "!chat", "!", "?"]) or
            any(k in content for k in ["삼성", "주가", "종가", "이평선", "매수", "매도", "전망", "목표가", "분석", "안녕"])
        )

        if not (is_briefing_cmd or is_chat_cmd):
            return

        # Handle Briefing Command
        if is_briefing_cmd:
            await self.handle_briefing_command(message)
            return

        # Handle AI Chat Query
        await self.handle_chat_command(message, content)

    async def handle_briefing_command(self, message: discord.Message):
        """Send daily stock briefing directly in Discord."""
        try:
            async with message.channel.typing():
                summary = self.data_service.get_summary()
                stats = self.data_service.get_statistics()
                m = summary.metrics

                color = 0x3b82f6
                if "상승" in summary.trend:
                    color = 0x10b981
                elif "하락" in summary.trend:
                    color = 0xf43f5e

                embed = discord.Embed(
                    title="📊 삼성전자(005930.KS) 시장 분석 일일 브리핑",
                    description=f"**분석 기간**: {summary.period} (총 {summary.count:,}개 거래일)",
                    color=color,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="📈 주가 핵심 지표",
                    value=(
                        f"• **최신 종가**: **{m.latest:,.0f}원**\n"
                        f"• **20일 추세**: {summary.trend}\n"
                        f"• **평균 종가**: {m.average:,.0f}원\n"
                        f"• **최고가/최저가**: {m.max:,.0f}원 / {m.min:,.0f}원"
                    ),
                    inline=False
                )

                if stats:
                    rsi = stats.get("rsi_14", 50.0)
                    signal_text = "🟡 중립 / 관망"
                    if rsi >= 70:
                        signal_text = "🔴 과열 / 분할 매도 고려 (RSI 과매수)"
                    elif rsi <= 30:
                        signal_text = "🟢 과매도 / 분할 매수 기회 (RSI 과매도)"
                    elif "상승" in summary.trend:
                        signal_text = "🟢 추세 상승 / 보유 및 추종"
                    elif "하락" in summary.trend:
                        signal_text = "🔴 단기 조정 / 비중 축소"

                    embed.add_field(
                        name="🎯 기술적 보조지표 & 매매 신호",
                        value=(
                            f"• **14일 RSI**: **{rsi:.1f}**\n"
                            f"• **20일 이평선(SMA 20)**: {stats.get('sma_20', 0):,.0f}원\n"
                            f"• **20일 변동성**: ±{stats.get('volatility', 0):,.0f}원\n"
                            f"• **판단 신호**: **{signal_text}**"
                        ),
                        inline=False
                    )

                embed.set_footer(
                    text="Samsung Stock AI Assistant • 양방향 Discord 봇",
                    icon_url="https://img.icons8.com/color/48/artificial-intelligence.png"
                )

                await message.reply(embed=embed)
        except Exception as e:
            logger.error(f"Error handling briefing in Discord bot: {e}")
            await message.reply(f"⚠️ 브리핑 생성 중 오류가 발생했습니다: {e}")

    async def handle_chat_command(self, message: discord.Message, raw_content: str):
        """Process user message through AI ChatService and reply."""
        # Strip bot mention or command prefix
        clean_text = raw_content
        if self.user in message.mentions:
            clean_text = clean_text.replace(f"<@{self.user.id}>", "").replace(f"<@!{self.user.id}>", "")
        for prefix in ["!질문", "!삼성", "!주가", "!ask"]:
            if clean_text.startswith(prefix):
                clean_text = clean_text[len(prefix):]
                break
        clean_text = clean_text.strip()

        if not clean_text:
            await message.reply("❓ 삼성전자 주가에 대해 궁금하신 점을 입력해주세요! (예: `!질문 최근 20일 추세와 지지선 분석해줘`)")
            return

        try:
            async with message.channel.typing():
                # Call AI chat service with live Firestore context injection
                response = await self.chat_service.chat(message=clean_text)

                color = 0x3b82f6
                trend_str = "보합 / 분석 중"
                if response.summary_used:
                    trend_str = response.summary_used.get("trend", trend_str)
                    if "상승" in trend_str:
                        color = 0x10b981
                    elif "하락" in trend_str:
                        color = 0xf43f5e

                embed = discord.Embed(
                    title="🤖 삼성전자(005930.KS) AI 분석 답변",
                    color=color,
                    timestamp=datetime.now(timezone.utc)
                )

                embed.add_field(
                    name="❓ 질문",
                    value=clean_text[:500],
                    inline=False
                )

                reply_text = response.reply
                if len(reply_text) > 1000:
                    reply_text = reply_text[:990] + "...\n*(전체 내용은 웹 화면 참조)*"

                embed.add_field(
                    name="💡 AI 맞춤 분석 (Fact • Why • Action)",
                    value=reply_text,
                    inline=False
                )

                if response.summary_used and "metrics" in response.summary_used:
                    m = response.summary_used["metrics"]
                    embed.add_field(
                        name="📊 실시간 주가 컨텍스트",
                        value=f"• 최신 종가: **{m.get('latest', 0):,.0f}원** | 20일 추세: **{trend_str}**",
                        inline=False
                    )

                embed.set_footer(
                    text=f"요청자: {message.author.display_name} • Gemini 2.5 Flash",
                    icon_url=message.author.display_avatar.url if hasattr(message.author, 'display_avatar') else None
                )

                await message.reply(embed=embed)
                print(f"[Discord Bot 회신 완료] {message.author}에게 AI 답변 임베드 카드 발송 성공")
        except Exception as e:
            logger.error(f"Error handling chat in Discord bot: {e}")
            await message.reply(f"⚠️ AI 답변 생성 중 오류가 발생했습니다: {e}")

_bot_instance: Optional[SamsungStockDiscordBot] = None
_bot_task: Optional[asyncio.Task] = None

def get_discord_bot() -> SamsungStockDiscordBot:
    global _bot_instance
    if _bot_instance is None:
        _bot_instance = SamsungStockDiscordBot()
    return _bot_instance

async def run_discord_bot_background(token: Optional[str] = None):
    """Launch the Discord bot in the background asyncio event loop."""
    bot_token = token or DISCORD_BOT_TOKEN
    if not bot_token:
        logger.info("[Discord Bot] DISCORD_BOT_TOKEN is not configured. Bot listener disabled.")
        return None

    try:
        logger.info("[Discord Bot] Connecting to Discord Gateway with bot token (full intents)...")
        bot = SamsungStockDiscordBot(with_message_content=True)
        await bot.start(bot_token)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("[Discord Bot] 'Message Content Intent' is not enabled in Developer Portal. Falling back to basic intents (mentions only)...")
        print("[Discord Bot ⚠️] 'Message Content Intent'가 꺼져 있어 멘션(@봇) 전용 모드로 안전하게 재연결합니다.")
        try:
            bot = SamsungStockDiscordBot(with_message_content=False)
            await bot.start(bot_token)
        except Exception as e2:
            logger.error(f"[Discord Bot] Fallback bot failed: {e2}")
    except Exception as e:
        logger.error(f"[Discord Bot] Failed to run Discord bot: {e}")
