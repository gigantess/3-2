# 📈 삼성전자(005930.KS) 주가 분석 AI 비서 (3-2 미션)

> **"일반적인 AI는 여러분의 데이터를 모릅니다. 여기 내 주가 데이터를 완벽히 이해하고 실시간으로 분석하는 전용 금융 AI 비서가 있습니다."**

본 프로젝트는 `3-1` 프로젝트에서 구축한 **삼성전자(005930.KS) 2024~2026년 주가 시계열 분석 데이터셋(656건)**과 **통계/추세 산출 알고리즘**을 계승하여, FastAPI 백엔드, Firebase Firestore 데이터베이스, OpenAI GPT 모델(컨텍스트 주입), 그리고 프레임워크 없는 순수 바닐라 HTML/CSS/JavaScript 웹 프론트엔드로 완성한 **데이터 기반 맞춤형 AI 비서 서비스**입니다.

---

## 🚀 배포 URL 정보

| 구분 | 플랫폼 | URL | 상태 |
| :--- | :--- | :--- | :--- |
| **웹 프론트엔드** | Vercel | `https://samsung-stock-ai-assistant.vercel.app` (예시) | Ready |
| **백엔드 API 서버** | Render | `https://samsung-stock-ai-assistant.onrender.com` (예시) | Ready |
| **Swagger API 명세서** | Render | `https://samsung-stock-ai-assistant.onrender.com/docs` | Live |

> **⚡ Render 무료 티어 콜드스타트 안내:**
> Render Free Tier 인스턴스는 15분간 비활성 시 슬립(Sleep) 모드로 전환됩니다. 첫 요청 시 인스턴스 기동에 약 30~50초의 지연이 발생할 수 있으며, 프론트엔드 상단에 안내 배너가 구현되어 있습니다.

---

## 🛠️ 기술 스택 (Tech Stack)

### 백엔드 (Backend)
- **FastAPI**: 비동기 고성능 RESTful API 프레임워크
- **Uvicorn**: ASGI 웹 서버
- **Pydantic v2**: 엄격한 요청/응답 데이터 스키마 유효성 검증
- **Firebase Firestore (`firebase-admin`)**: NoSQL 클라우드 데이터베이스 (`data`, `conversations` 컬렉션)
  - *로컬 개발 및 키 부재 시 자동 지원되는 파일 기반 In-Memory Mock DB Fallback 내장*
- **OpenAI API (`gpt-4o-mini`)**: 시스템 프롬프트 컨텍스트 주입 및 도구 호출(Function Calling) 지원
- **Pandas**: 대용량 시계열 데이터 처리 및 3-1 데이터 마이그레이션

### 프론트엔드 (Frontend)
- **HTML5 & Vanilla CSS**: 모던 다크/라이트 테마 시스템, 글래스모피즘(Glassmorphism), 부드러운 트랜지션
- **Vanilla JavaScript (ES6+)**: 프레임워크 없는 모듈형 아키텍처, 비동기 상태 관리
- **Chart.js (CDN)**: 삼성전자 일별 종가 및 20일 이동평균선(SMA 20) 반응형 인터랙티브 차트

### 배포 및 테스트
- **Render**: 백엔드 컨테이너 / Python 서비스 배포 (`render.yaml`, `Dockerfile`)
- **Vercel**: 바닐라 프론트엔드 정적 호스팅 (`vercel.json`)
- **Pytest**: 100% 통과된 단위/통합 테스트 스위트 (`tests/`)

---

## 🌟 주요 기능 및 3-1 결과물 연계

### 1. 3-1 시계열 데이터셋 완벽 연계 (`data/samsung_stock_2024_present.csv`)
- 2024년 1월 2일부터 2026년 9월 11일까지의 **656개 거래일 실데이터**를 Firestore `data` 컬렉션에 `(date, value, memo)` 포맷으로 일괄 마이그레이션.
- `date`: 거래일자 (YYYY-MM-DD)
- `value`: 종가 (원 단위 정수)
- `memo`: 시가, 고가, 저가, 거래량 등 메타정보 보존

### 2. 실시간 통계 산출 및 컨텍스트 주입 (Context Injection)
- 사용자가 질문할 때마다 백엔드가 `/api/data/summary`를 자동 호출하여 현재 데이터베이스의 기간, 건수, 평균/최고/최저가, 최근 20일 이동평균선 대비 추세율을 계산.
- 계산된 요약 정보를 GPT의 시스템 프롬프트에 동적 삽입함으로써, AI가 환각(Hallucination) 없이 사용자의 실제 주가 데이터를 바탕으로 정확한 수치와 분석 조언을 제공.

### 3. 데이터 관리 (CRUD)
- `POST /api/data`: 새 시계열 데이터 추가 (날짜 정규식 검증)
- `GET /api/data`: 데이터 목록 조회 (정렬, 페이지네이션 지원)
- `PUT /api/data/{id}`: 데이터 수정
- `DELETE /api/data/{id}`: 데이터 삭제
- `GET /api/data/export`: CSV 및 JSON 다운로드 (보너스 과제)

### 4. 대화 세션 관리 및 불러오기 UX
- AI 대화 시 대화 내용이 `conversations` 컬렉션에 자동 저장.
- 사이드바에 과거 대화 목록 표시 및 클릭 시 이전 대화 메시지 즉시 복원.
- 불필요한 대화 삭제 기능 제공.

### 5. 인터랙티브 시각화 및 UX 고도화 (보너스 과제 2)
- Chart.js를 이용한 일별 종가 및 20일 이동평균선(SMA 20) 추세 시각화.
- 심층 통계 API (`GET /api/data/statistics`): 20일 변동성(표준편차), 60일 이동평균, 14일 RSI, 최고/최저가 및 누적 수익률 제공.
- 데이터 내보내기: CSV 및 JSON 파일 즉시 다운로드 (`/api/data/export`).
- 다크 모드 / 라이트 모드 원클릭 토글 (localStorage 영구 저장).
- 빠른 질문을 위한 퀵 프롬프트 칩(Chips).

### 6. AI 도구 호출 (Function Calling) & MCP Server 연동 (보너스 과제 1)
- **OpenAI Function Calling**: GPT가 상세 데이터나 통계 조회가 필요할 때 `get_data_summary`, `get_data_statistics`, `get_recent_data_items` 도구를 자동 호출.
- **Model Context Protocol (MCP) Server**: `backend/mcp_server.py`를 통해 외부 AI 에이전트(Claude Desktop 등)에서 표준 JSON-RPC 프로토콜로 삼성전자 주가 데이터를 직접 조회 가능.
  - 도구 호출 근거: 정밀 수치 분석이나 기간별 통계 계산 시 환각을 방지하고 백엔드의 검증된 알고리즘을 사용하기 위해 내부 API 도구를 호출.
  - 호출 흐름: `User Query` → `GPT 판단` → `Tool Call Request` → `FastAPI/DataService 실행` → `Tool Output` → `GPT 최종 맞춤형 답변 반환`.

---

## 📁 디렉토리 구조

```
3-2/
├── backend/
│   ├── __init__.py
│   ├── config.py              # 환경 변수 및 설정
│   ├── database.py            # Firestore 및 Fallback Mock DB
│   ├── main.py                # FastAPI 앱 엔트리포인트 & CORS
│   ├── schemas/               # Pydantic 데이터 모델
│   │   ├── chat.py
│   │   ├── conversation.py
│   │   └── data.py
│   ├── services/              # 비즈니스 로직
│   │   ├── chat_service.py    # 프롬프트 주입 및 OpenAI 연동
│   │   ├── conversation_service.py # 대화 세션 관리
│   │   └── data_service.py    # 3-1 통계 알고리즘 및 CRUD
│   ├── routers/               # REST API 엔드포인트
│   │   ├── chat.py
│   │   ├── conversations.py
│   │   └── data.py
│   └── scripts/
│       └── seed_data.py       # 3-1 CSV -> DB 마이그레이션 CLI
├── data/
│   └── samsung_stock_2024_present.csv # 3-1 삼성전자 656건 원본 데이터
├── frontend/                  # 바닐라 프론트엔드
│   ├── index.html             # 시맨틱 반응형 웹 레이아웃
│   ├── styles.css             # 글래스모피즘 & 테마 CSS
│   ├── config.js              # 동적 API_BASE_URL 처리
│   └── app.js                 # 상태 관리, 차트 및 API 통신
├── tests/                     # Pytest 테스트 스위트
│   ├── test_api_chat.py
│   ├── test_api_conversations.py
│   └── test_api_data.py
├── doc/
│   └── mission.md             # 과제 요구사항 명세서
├── Dockerfile                 # 도커 컨테이너 빌드 파일
├── render.yaml                # Render 배포 청사진
├── vercel.json                # Vercel 배포 설정 파일
├── requirements.txt           # Python 의존성 패키지
└── README.md                  # 프로젝트 안내 문서
```

---

## 💻 로컬 실행 가이드 (Quick Start)

### 1. 환경 설정 및 가상환경 준비

```powershell
# 가상환경 생성 및 활성화
python -m venv venv
.\venv\Scripts\Activate.ps1

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (`.env`)

프로젝트 루트에 `.env` 파일을 생성하고 필요한 환경 변수를 입력합니다:

```ini
GEMINI_API_KEY=your_gemini_api_key_here
FIREBASE_SERVICE_ACCOUNT_JSON=firebase-credentials.json
FIREBASE_PROJECT_ID=your-project-id
ALLOWED_ORIGINS=*
PORT=8000
HOST=0.0.0.0
```

> **참고:** Gemini API 키나 Firebase 키가 없더라도 시스템에 내장된 **Mock Fallback 모드**가 작동하여 로컬 개발, 화면 조작, 테스트를 문제없이 수행할 수 있습니다.

### 3. 3-1 데이터셋 시딩 (Database Seeding)

```powershell
python backend/scripts/seed_data.py --limit 656
```

### 4. 서버 실행

```powershell
# FastAPI 서버 기동 (프론트엔드 정적 파일 자동 서빙 포함)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

- 웹 브라우저에서 `http://127.0.0.1:8000` 접속
- API 문서(Swagger UI) 확인: `http://127.0.0.1:8000/docs`

### 5. 테스트 실행

```powershell
pytest tests/ -v
```

---

## 📸 제출 스크린샷 가이드

과제 제출 시 아래 3가지 주요 화면을 캡처하여 첨부합니다:

1. **데이터 요약이 보이는 채팅 화면**:
   - 상단 KPI 요약 카드(분석 기간, 최신 종가, 최고/최저가, 최근 트렌드)와 함께 사용자의 질문 및 데이터 수치가 반영된 AI 답변이 표시된 화면.
2. **데이터 관리 화면 (CRUD)**:
   - "데이터 관리 (CRUD)" 탭에서 일별 주가 목록 테이블, 페이징 바, 새 데이터 추가 모달 동작이 확인되는 화면.
3. **대화 기록 화면**:
   - 사이드바의 이전 대화 목록에서 특정 대화를 클릭하여 과거 질의응답 내역이 채팅창에 재표시되는 화면.
