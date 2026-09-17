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

from backend.config import DISCORD_BOT_TOKEN
from backend.services.discord_bot import get_discord_bot

def main():
    parser = argparse.ArgumentParser(description="Run Samsung Stock AI Discord Bot")
    parser.add_argument("--token", type=str, default=None, help="Discord Bot Token")
    args = parser.parse_args()

    token = args.token or DISCORD_BOT_TOKEN
    if not token:
        print("\n❌ [오류] DISCORD_BOT_TOKEN이 설정되어 있지 않습니다.")
        print("1. Discord Developer Portal (https://discord.com/developers/applications) 접속")
        print("2. [New Application] 생성 -> [Bot] 탭 -> [Reset Token]으로 토큰 복사")
        print("3. [Privileged Gateway Intents] 섹션에서 'MESSAGE CONTENT INTENT' 활성화 필수")
        print("4. .env 파일에 DISCORD_BOT_TOKEN=<토큰> 추가 또는 --token 옵션으로 전달\n")
        sys.exit(1)

    print("🚀 [Discord Bot] 삼성전자 주가 분석 AI 비서 봇 연결 시작...")
    bot = get_discord_bot()
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ [Discord Bot] 실행 오류: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
