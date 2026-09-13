import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.config import ALLOWED_ORIGINS, PORT, HOST
from backend.routers import data, conversations, chat
from backend.services.data_service import DataService

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Auto-seed on startup if empty
    try:
        ds = DataService()
        items, count = ds.get_items(limit=1)
        if count == 0:
            csv_path = Path(__file__).resolve().parent.parent / "data" / "samsung_stock_2024_present.csv"
            if csv_path.exists():
                from backend.scripts.seed_data import seed_database
                print("[Startup] Database is empty. Automatically seeding 3-1 dataset...")
                seed_database(limit=656)
    except Exception as e:
        print(f"[Startup Warning] Could not check/seed database: {e}")
    yield

app = FastAPI(
    title="삼성전자 주가 분석 AI 비서 API",
    description="3-1 시계열 분석 결과를 계승한 데이터 기반 맞춤형 AI 비서 서비스 (FastAPI + Firestore + OpenAI)",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS if ALLOWED_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)

@app.get("/health", tags=["Health"])
def health_check():
    """
    서버 및 데이터베이스 상태를 확인하는 헬스체크 엔드포인트
    """
    ds = DataService()
    summary = ds.get_summary()
    return {
        "status": "healthy",
        "service": "samsung-stock-ai-assistant",
        "data_count": summary.count,
        "period": summary.period
    }



# Frontend static serving
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend_root():
        index_file = FRONTEND_DIR / "index.html"
        if index_file.exists():
            return FileResponse(str(index_file))
        return {"message": "삼성전자 주가 분석 AI 비서 API가 실행 중입니다. /docs 에서 API 문서를 확인하세요."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=HOST, port=PORT, reload=True)
