"""
Samsung Stock AI Analyst - Discord Bot Daemon
Listens for user messages in Discord and replies in real-time with AI analysis.

Usage:
    python backend/scripts/run_discord_bot.py
    python backend/scripts/run_discord_bot.py --token YOUR_BOT_TOKEN
"""
import sys
import os
import argparse
import asyncio
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from backend.config import DISCORD_BOT_TOKEN
from backend.services.discord_bot import SamsungStockDiscordBot
import discord

def main():
    parser = argparse.ArgumentParser(description="Run Samsung Stock AI Discord Bot")
    parser.add_argument("--token", type=str, default=None, help="Discord Bot Token")
    args = parser.parse_args()

    token = args.token or DISCORD_BOT_TOKEN
    if not token:
        print("\n❌ [오류] DISCORD_BOT_TOKEN이 설정되어 있지 않습니다.")
        print("1. Discord Developer Portal (https://discord.com/developers/applications) 접속")
        print("2. [New Application] 생성 -> [Bot] 탭 -> [Reset Token]으로 토큰 복사")
        print("3. [Privileged Gateway Intents] 섹션에서 'MESSAGE CONTENT INTENT' 활성화")
        print("4. .env 파일에 DISCORD_BOT_TOKEN=<토큰> 추가 또는 --token 옵션으로 전달\n")
        sys.exit(1)

    print("🚀 [Discord Bot] 삼성전자 주가 분석 AI 비서 봇 연결 시작...")
    try:
        bot = SamsungStockDiscordBot(with_message_content=True)
        bot.run(token)
    except discord.errors.PrivilegedIntentsRequired:
        print("\n⚠️ [안내] Discord Developer Portal에서 'MESSAGE CONTENT INTENT'가 활성화되지 않았습니다.")
        print("➡️ 봇을 멘션(@삼성전자 AI 비서) 전용 모드로 안전하게 재가동합니다.")
        print("💡 일반 텍스트 '!질문' 명령어를 사용하시려면 개발자 포털 [Bot] 탭에서 'MESSAGE CONTENT INTENT'를 켜주세요.\n")
        try:
            bot = SamsungStockDiscordBot(with_message_content=False)
            bot.run(token)
        except Exception as e2:
            print(f"❌ [Discord Bot] 재실행 실패: {e2}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ [Discord Bot] 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
