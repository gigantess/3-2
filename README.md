# 📈 삼성전자(005930.KS) 주가 분석 AI 비서 (3-2 미션)

> **"일반적인 AI는 여러분의 데이터를 모릅니다. 여기 내 주가 데이터를 완벽히 이해하고 실시간으로 분석하는 전용 금융 AI 비서가 있습니다."**

본 프로젝트는 `3-1` 프로젝트에서 구축한 **삼성전자(005930.KS) 2024~2026년 주가 시계열 분석 데이터셋(656건)**과 **통계/추세 산출 알고리즘**을 계승하여, FastAPI 백엔드, Firebase Firestore 데이터베이스, OpenAI GPT 모델(컨텍스트 주입), 그리고 프레임워크 없는 순수 바닐라 HTML/CSS/JavaScript 웹 프론트엔드로 완성한 **데이터 기반 맞춤형 AI 비서 서비스**입니다.

---

## 🚀 배포 URL 정보

| 구분 | 플랫폼 | URL | 상태 |
| :--- | :--- | :--- | :--- |
| **웹 프론트엔드** | Vercel | `https://3-2-1-gigantess1.vercel.app/` | Ready |
| **백엔드 API 서버** | Render | `https://samsung-stock-ai-assistant.onrender.com` | Live |
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

## 🏗️ 시스템 아키텍처 및 핵심 솔루션 역할 (Solution Roles)

본 프로젝트는 각 솔루션이 명확한 단일 책임(Single Responsibility)을 가지는 **클라우드 네이티브 4계층 아키텍처**로 설계되었습니다.

```
[ 클라이언트 브라우저 (사용자) ]
       │
       ▼
┌────────────────────────────────────────────────────────┐
│ 1. 웹 프론트엔드 계층 (Vercel)                          │
│  - 순수 Vanilla HTML5 / CSS3 / JavaScript (ES6+)       │
│  - Chart.js 인터랙티브 시계열 차트 시각화                │
│  - 백엔드 연결 설정 모달 (Render API URL 동적 연동)      │
└────────────────────────────────────────────────────────┘
       │ REST API (JSON 통신, CORS 허용)
       ▼
┌────────────────────────────────────────────────────────┐
│ 2. 백엔드 서비스 계층 (Render - FastAPI)                │
│  - 비동기 고성능 REST API & Swagger UI (/docs)         │
│  - 3-1 금융 시계열 통계 엔진 (SMA 20/60, RSI, 변동성)     │
│  - 컨텍스트 파이프라인 및 MCP Server 표준 프로토콜 호스팅 │
└──────────────┬──────────────────────────┬──────────────┘
               │                          │
        시계열 데이터 쿼리           컨텍스트 주입 & 대화
        대화 히스토리 영구 저장      (Context Injection)
               │                          │
               ▼                          ▼
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ 3. 데이터 및 메모리 계층     │  │ 4. 지능 및 추론 계층        │
│    (Firebase Firestore)      │  │    (Google Gemini API)       │
│  - 'data': 656건 주가 시계열 │  │  - gemini-2.5-flash 모델     │
│  - 'conversations': 대화로그 │  │  - 도구 호출(Function Call)  │
│  - AI 컨텍스트 원천 데이터   │  │  - 정밀 수치 기반 금융 분석  │
└──────────────────────────────┘  └──────────────────────────────┘
```

### 1. Google Cloud Firestore: 단순 저장소를 넘어선 '컨텍스트 엔진 & 대화 메모리'
파이어스토어는 정적 데이터를 보관하는 데이터베이스 이상의 핵심 기능을 수행합니다:
1. **AI 지능을 부여하는 '실시간 컨텍스트 제공원' (Context Engine)**:
   - 일반 LLM은 사용자의 주가 데이터를 알지 못합니다.
   - 사용자가 질문을 던질 때마다 백엔드가 Firestore의 `data` 컬렉션을 즉시 조회하여 **평균/최고/최저가, 최근 20일 이동평균선(SMA 20) 추세율을 계산하고 시스템 프롬프트에 주입**합니다.
   - 이를 통해 AI의 거짓말(환각, Hallucination)을 원천 차단하고 실제 데이터 수치 기반의 신뢰성 높은 금융 답변을 생성합니다.
2. **세션 간 연속성을 보장하는 '장기 대화 메모리' (Long-term Memory)**:
   - 사용자와 AI가 나눈 모든 문답이 `conversations` 컬렉션에 영구 저장됩니다.
   - 브라우저를 재부팅하거나 재접속하더라도 사이드바에서 과거 대화 세션을 클릭하면 파이어스토어에서 메시지 히스토리를 즉각 복원합니다.
3. **실시간 데이터 무결성 및 CRUD 상태 관리**:
   - 웹 화면에서 신규 주가를 등록/수정/삭제하는 즉시 Firestore에 동기화되며, KPI 요약 바, Chart.js 시계열 그래프, AI가 인지하는 최신 종가가 실시간으로 함께 갱신됩니다.
4. **고급 금융 지표 및 도구 호출(Function Calling)의 원천**:
   - 20일 변동성(표준편차), 60일 이동평균, 14일 RSI 지표 산출과 CSV/JSON 내보내기, MCP 도구 조회의 기초 원천으로 활용됩니다.

### 2. Render 백엔드: 비동기 비즈니스 로직 & AI 파이프라인 호스팅
- **역할**: 파이썬 FastAPI 웹 서버, 3-1 금융 분석 알고리즘, Firestore SDK, Gemini API 클라이언트, 표준 MCP 서버를 구동하는 **서비스의 두뇌 엔진**.
- **Render 백엔드 URL의 필요성**:
  - Vercel에 배포된 정적 프론트엔드는 데이터베이스에 직접 접근할 권한이나 AI 키를 갖고 있지 않습니다(보안상 브라우저 노출 금지).
  - 따라서 프론트엔드는 반드시 **Render 백엔드 URL(`https://[서비스이름].onrender.com`)**을 통해 정제된 데이터(`/api/data`)와 AI 답변(`/api/chat`)을 받아와야 합니다.
  - Vercel 웹 화면 상단의 **[API 연결 대기 중...]** 배지를 클릭하면 나타나는 **'백엔드 API 서버 연결 모달'**에 Render URL을 1회 설정함으로써 브라우저가 해당 백엔드를 바라보도록 동적 연결됩니다.
- **슬립 모드(Cold Start) 대응**: Render 무료 티어의 15분 미사용 후 슬립 특성을 감안하여, 프론트엔드 상단에 콜드스타트 안내 배너 및 헬스체크 폴백 로직이 내장되어 있습니다.

### 3. Vercel 프론트엔드: 바닐라 웹 UI & 반응형 시각화 호스팅
- **역할**: 외부 프레임워크(React/Tailwind 등) 일체 없이 순수 HTML5/CSS3/JavaScript로 제작된 프론트엔드를 전 세계 CDN 엣지 네트워크로 초고속 배포.
- **주요 구성**: AI 채팅 인터페이스, Chart.js 시계열 반응형 캔버스, 주가 CRUD 관리 모달, 다크/라이트 테마 토글, 실시간 백엔드 연결 설정 모달.

### 4. Google Gemini API (`google-genai`): 금융 데이터 특화 맞춤형 분석 추론
- **역할**: `gemini-2.5-flash` 최신 모델을 활용하여, 주입된 Firestore 요약 데이터와 사용자의 질문 의도를 결합해 **사실(Fact) - 원인 분석(Why) - 전략적 조언(Action)** 구조로 완성도 높은 금융 답변 제공.
- **도구 호출 (Function Calling)**: 정밀 통계나 최근 거래일 데이터 조회가 필요할 때 정의된 도구 스키마를 자율적으로 호출.

---

## ✅ 미션 요구사항 달성 현황표 (Mission Checklist)

`doc/mission.md`에 정의된 모든 핵심 요구사항 및 보너스 미션의 구현 및 검증 현황입니다.

| 범주 | 요구사항 항목 | 세부 내용 및 구현 위치 | 달성 여부 |
| :--- | :--- | :--- | :---: |
| **1. 개발 환경** | Python 3.10+ & 패키지 구성 | `fastapi`, `uvicorn`, `firebase-admin`, `google-genai`/`openai`, `python-dotenv`, `pandas`, `pytest` 구성 (`requirements.txt`) | **달성 (100%)** |
| | Firebase 자격증명 관리 | `.security/firebase-credentials.json` 및 환경 변수(`FIREBASE_SERVICE_ACCOUNT_JSON`, `FIREBASE_PROJECT_ID`) 보안 로드 (`backend/config.py`) | **달성 (100%)** |
| | 로컬 & 클라우드 배포 환경 | Render 백엔드 청사진(`render.yaml`) 및 Vercel 정적 호스팅(`vercel.json`) 구성 | **달성 (100%)** |
| **2. 데이터 선정/분석** | 100개 이상의 시계열 데이터 | 3-1 프로젝트의 삼성전자 2024~2026년 주가 실데이터 **656개 거래일** 적재 (`data/samsung_stock_2024_present.csv`) | **달성 (100%)** |
| | 요약 정보 및 트렌드 산출 | 기간, 레코드 건수, 평균/최고/최저/최신가 및 20일 이동평균 기반 추세율 알고리즘 구현 (`DataService.get_summary()`) | **달성 (100%)** |
| **3. FastAPI 구성** | 앱 초기화 및 CORS 설정 | `CORSMiddleware` 적용(`ALLOWED_ORIGINS`), 로컬 및 Vercel 도메인 연동 지원 (`backend/main.py`) | **달성 (100%)** |
| | 자동 문서화 및 정적 마운트 | Swagger UI(`/docs`) 및 ReDoc(`/redoc`), 루트 정적 자산 서빙 구현 | **달성 (100%)** |
| **4. Firestore 연동** | NoSQL 클라우드 DB 연동 | GCP Cloud Firestore 실제 연결 검증 및 In-Memory Mock DB Fallback 안전장치 내장 (`backend/database.py`) | **달성 (100%)** |
| | 컬렉션 구조 설계 | `data` (시계열 주가) 및 `conversations` (대화 기록) 컬렉션 2계층 분리 설계 | **달성 (100%)** |
| **5. 데이터 API (CRUD)** | `POST /api/data` | 새 데이터 추가 (날짜 정규식 검증, 종가 양수 검증 Pydantic 스키마) | **달성 (100%)** |
| | `GET /api/data` | 데이터 목록 조회 (날짜/수치 정렬, limit/offset 페이지네이션) | **달성 (100%)** |
| | `PUT /api/data/{id}` | 특정 ID의 시계열 레코드 수정 | **달성 (100%)** |
| | `DELETE /api/data/{id}` | 특정 ID의 시계열 레코드 삭제 | **달성 (100%)** |
| | `GET /api/data/summary` | 시스템 프롬프트 주입용 시계열 핵심 요약 및 인사이트 조회 | **달성 (100%)** |
| **6. 대화 기록 API** | `POST /api/conversations` | 대화 세션 및 메시지 히스토리 저장 | **달성 (100%)** |
| | `GET /api/conversations` | 이전 대화 세션 목록 조회 | **달성 (100%)** |
| | `GET /api/conversations/{id}`| 특정 대화 세션의 전체 메시지 내역 불러오기 | **달성 (100%)** |
| | `DELETE /api/conversations/{id}`| 대화 세션 삭제 | **달성 (100%)** |
| **7. AI 챗봇 (컨텍스트 주입)** | `POST /api/chat` | 사용자 질의 수신 → `/api/data/summary` 조회 → 시스템 프롬프트에 주입 → LLM 생성 → 대화 자동 저장 파이프라인 | **달성 (100%)** |
| | 사실 기반 맞춤형 응답 | 주가 수치(원 단위 쉼표), 원인 분석(Why), 행동 조언(Action) 구조화 답변 | **달성 (100%)** |
| **8. 웹 프론트엔드 (바닐라)** | 순수 바닐라 HTML/CSS/JS | React/Vue/Tailwind 일체 미사용, 시맨틱 HTML5와 커스텀 CSS/JS 구현 (`frontend/`) | **달성 (100%)** |
| | 채팅 UI & 로딩 인디케이터 | 사용자/어시스턴트 메시지 버블, 타이핑 로딩 애니메이션, 에러 토스트 | **달성 (100%)** |
| | 데이터 관리 (CRUD) 화면 | 일별 주가 목록 테이블, 모달 창을 통한 새 데이터 추가 및 삭제/수정 동작 | **달성 (100%)** |
| | 대화 기록 UX | 사이드바 대화 히스토리 목록 및 클릭 시 이전 대화 즉각 재표시 | **달성 (100%)** |
| | 데이터 요약 상단 바 | 분석 기간, 최신 종가, 최고/최저가, 최근 트렌드 배지 실시간 표시 | **달성 (100%)** |
| **9. 배포 및 운영** | Render 백엔드 배포 | `render.yaml` 블루프린트, 무료 티어 콜드스타트 대비 프론트엔드 안내 배너 구비 | **달성 (100%)** |
| | Vercel 프론트엔드 배포 | `vercel.json` 클린 URL 라우팅 및 `config.js`를 통한 API URL 동적 연동 | **달성 (100%)** |
| **🌟 보너스 1-A** | AI 도구 호출 (Function Calling)| `chat_service.py`에 `get_data_summary`, `get_data_statistics`, `get_recent_data_items` 도구 스키마 정의 | **달성 (100%)** |
| **🌟 보너스 1-B** | MCP Server 연동 | `backend/mcp_server.py` 표준 JSON-RPC 2.0 stdio 인터페이스 구현 (Claude Desktop/에이전트 연동) | **달성 (100%)** |
| **🌟 보너스 2-A** | 심층 통계 API (`/statistics`) | 20일 변동성(표준편차), 20/60일 이동평균선, 14일 RSI 지표 산출 엔드포인트 구현 | **달성 (100%)** |
| **🌟 보너스 2-B** | 시계열 인터랙티브 차트 | Chart.js 기반 일별 종가 라인 및 20일 이동평균선 반응형 캔버스 렌더링 | **달성 (100%)** |
| **🌟 보너스 2-C** | 데이터 내보내기 (Export) | `/api/data/export?format=csv|json` 파일 다운로드 기능 및 웹 버튼 제공 | **달성 (100%)** |
| **🌟 보너스 2-D** | 다크 모드 토글 (Theme) | 헤더 테마 전환 버튼 및 `localStorage` 기반 상태 영구 유지 | **달성 (100%)** |
| **🌟 품질 검증 (TDD)**| 테스트 스위트 (Pytest) | API, 비즈니스 로직, Gemini 연동 등 9개 테스트 전 항목 통과 (100%) | **달성 (100%)** |

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
