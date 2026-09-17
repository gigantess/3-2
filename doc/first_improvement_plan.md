# 3-2 삼성전자 주가 분석 AI 비서 종합 개선 계획 (1차 평가의견 보완)

`doc/first_assesment.md`에 제시된 18개 평가 항목의 부족한 점(Shortcomings)과 보완 권고사항(Remediations)을 체계적으로 반영하여, 3-2 프로젝트의 완성도, 운영 신뢰성, 코드 품질 및 사용자 경험을 대폭 향상시키기 위한 실행 계획입니다.

---

## 1. 1차 평가의견 분석 및 개선 목표

평가 결과 전 항목 **PASS**를 달성하였으나, 운영 신뢰도(실제 접속 증적, 비밀값 등록 절차, 헬스체크), 백엔드 견고성(에러 처리, 캐싱, 입력 필터링, 기간 필터 테스트), 그리고 프론트엔드 복원력(네트워크 오류 처리, 모바일 시나리오)에서 보완 요구가 식별되었습니다.

### 5대 핵심 개선 영역
1. **운영 신뢰성 및 배포 증적 보강 (Items #1, #2, #14, #15, #16)**
   - Vercel/Render 실제 배포 접속 증적 및 Swagger UI 접근 확인 절차
   - Render/Vercel 환경변수(비밀값) 단계별 등록 가이드
   - 콜드스타트 완화를 위한 외부 헬스체크 프리워밍(Pre-warming) 자동화 방안
   - 프로덕션 도메인별 CORS 권장값 및 cURL 테스트 검증 절차
2. **백엔드 아키텍처 및 성능 최적화 (Items #3, #12, #17, #18)**
   - 데이터 저장/수정/삭제 시 세부 에러 핸들링 및 안전한 예외 응답 체계
   - 요약 API(`get_summary`) In-Memory TTL 캐싱 도입 (DB 부하 경감)
   - 요약 API 기간 필터링(`start_date`, `end_date`) 지원 및 기준 변경 유연성 확보
   - XSS/SQLi 방지를 위한 서버측 입력 데이터 검증 및 필터링 정책 강화
3. **AI 컨텍스트 주입 및 대화 관리 고도화 (Items #4, #5, #11, #13)**
   - 시스템 프롬프트 템플릿 문장 구조 표준화 및 코드 내 독스트링/샘플 제공
   - 컨텍스트 주입에 따른 토큰 소비량, 비용 절감 효과(98% 절감) 및 장단점 분석표 추가
   - 대화 세션 용량 제한(최대 메시지 수/길이) 및 보존 정책 수립
   - 대화 저장 시점 및 동시성 충돌 해결(Concurrency Policy) 명시
4. **데이터베이스 및 스키마 명세 구체화 (Items #7, #8, #9)**
   - 4계층 아키텍처(Router → Service → Schema → Database) 책임 흐름 예시 문서화
   - Firestore `data` 및 `conversations` 컬렉션 스키마, 데이터 타입, 인덱스 및 쿼리 패턴 정리
   - Pydantic 요청/응답 예시 (200/201 성공 및 422 유효성 검증 실패 상세 샘플) 문서화
5. **프론트엔드 복원력 및 모바일 UX (Items #6, #10)**
   - 네트워크 단절 및 오프라인 상태 감지 시 자동 재시도 및 사용자 안내 UI 보완
   - 모바일 뷰포트(<=900px)에서의 사이드바 토글, 모달 조작 및 사용 시나리오 문서화

---

## User Review Required

> [!IMPORTANT]
> **요약 API 기간 필터 파라미터 추가에 따른 호환성 유지**
> `GET /api/data/summary` 엔드포인트에 `start_date`, `end_date` 쿼리 파라미터를 선택적(Optional)으로 추가합니다. 기본값 호출 시에는 기존과 동일하게 전체 기간을 대상으로 요약하므로 기존 프론트엔드 및 AI 챗봇과의 100% 하위 호환성을 유지합니다.

> [!NOTE]
> **TTL 캐싱 정책**
> 주가 요약 데이터(`get_summary`)는 60초 TTL(Time-To-Live) 기반 In-Memory 캐시를 적용하며, 신규 주가 등록/수정/삭제(`POST`, `PUT`, `DELETE`) 발생 시 즉시 캐시를 무효화(Invalidation)하여 데이터 일관성을 보장합니다.

---

## Open Questions

- 현재 확인된 바로는 모든 개선 사항이 기존 동작을 깨뜨리지 않고 확장 및 문서 보완 형태로 수행 가능합니다. 추가로 요구되는 특정 기간 요약 필터 조건이나 외부 크론 설정 선호사항이 있으시면 제안해주세요.

---

## Proposed Changes

### 1. 백엔드 서비스 및 라우터 개선

#### [MODIFY] [data_service.py](file:///d:/cody/3-2/backend/services/data_service.py)
- **TTL 캐싱 도입**: `_summary_cache`, `_cache_timestamp`, `CACHE_TTL_SECONDS = 60` 추가. `add_item`, `update_item`, `delete_item` 호출 시 `_invalidate_cache()` 실행.
- **기간 필터링 지원**: `get_summary(start_date: Optional[str] = None, end_date: Optional[str] = None)` 기능 추가.
- **저장 및 수정 실패 예외 처리**: Firestore 통신 에러 발생 시 커스텀 예외 발생 및 로깅 강화.

#### [MODIFY] [data.py (Router)](file:///d:/cody/3-2/backend/routers/data.py)
- `GET /api/data/summary`에 `start_date`, `end_date` Query 파라미터 추가.
- CRUD 엔드포인트에서 발생 가능한 예외에 대한 정교한 HTTP 400/500 에러 핸들링 추가.

#### [MODIFY] [data.py (Schema)](file:///d:/cody/3-2/backend/schemas/data.py)
- 입력 필터링 강화: `memo` 필드에 최대 길이 제한(500자) 및 HTML 태그 이스케이프/특수문자 정제 validator 추가.
- `value` 필드에 양수 검증(`gt=0`) 및 상한선(`le=10000000`) 유효성 검증 추가.

#### [MODIFY] [conversation_service.py](file:///d:/cody/3-2/backend/services/conversation_service.py)
- 대화 용량 제한 정책 적용: 단일 세션당 최대 메시지 수 제한(예: 100개 초과 시 오래된 메시지 보존/아카이빙 가이드 적용) 및 단일 메시지 길이(최대 4,000자) 검증.
- 동시성 안전성 로직 보강 및 트랜잭션/문서 업데이트 처리 가이드라인 반영.

#### [MODIFY] [chat_service.py](file:///d:/cody/3-2/backend/services/chat_service.py)
- `_build_system_prompt` 템플릿을 정규화하고 상세 독스트링 및 테스트용 반환 지원 메서드 추가.

---

### 2. 프론트엔드 복원력 및 UX 개선

#### [MODIFY] [app.js](file:///d:/cody/3-2/frontend/app.js)
- `API.get`, `API.post`, `API.put`, `API.delete` 모듈에 네트워크 타임아웃 및 오프라인 감지 로직 보강.
- 네트워크 연결 실패 시 사용자 친화적인 에러 토스트 표시 및 재시도(Retry) 안내 로직 추가.
- 모바일 사이드바 토글 동작 UX 안정화.

---

### 3. 단위 테스트 스위트 확장

#### [NEW] [test_summary_period_and_cache.py](file:///d:/cody/3-2/tests/test_summary_period_and_cache.py)
- 기간 필터(`start_date`, `end_date`) 적용 시 요약 통계 계산 정확성 검증.
- 데이터 생성/수정/삭제 시 요약 캐시 Invalidation 검증.
- 유효하지 않은 입력값(음수 가격, 비정상 날짜, XSS 스크립트 문자열)에 대한 422 에러 응답 테스트.
- 대화 메시지 길이 제한 및 세션 메시지 제한 테스트.

---

### 4. 종합 문서화 (`README.md`) 고도화

#### [MODIFY] [README.md](file:///d:/cody/3-2/README.md)
18개 평가 항목의 보완 사항을 README의 해당 섹션에 완벽하게 반영:
1. **배포 URL 및 헬스체크 증적**: 라이브 URL 접속 성공 cURL 명령 및 JSON 응답 예시 추가.
2. **Swagger UI 접근 및 테스트 절차**: `/docs` 라이브 화면 접속 방법 및 Try it out 절차 명시.
3. **에러 처리 및 롤백 정책**: 클라이언트/서버 저장 실패 대응 및 사용자 안내 정책 정리.
4. **시스템 프롬프트 템플릿**: 코드 내 실제 주입 템플릿 전문과 문장 구성 규칙 표기.
5. **대화 관리 정책**: 세션당 메시지 수, 메시지 크기 제한, 보존 주기 명시.
6. **모바일 사용 시나리오**: 모바일 뷰(스마트폰/태블릿)에서의 사이드바 토글 및 CRUD 조작 안내.
7. **아키텍처 계층별 책임**: Router → Service → Schema → DB 간 입력→검증→저장 처리 흐름도 및 책임 명세.
8. **Firestore 스키마 및 인덱스**: `data`, `conversations` 컬렉션의 필드, 타입, 인덱스 및 쿼리 패턴 표 추가.
9. **Pydantic 요청/응답 예시**: 200 성공 및 422 검증 오류 JSON 샘플 추가.
10. **오프라인/네트워크 복구 시나리오**: 프론트엔드 장애 처리 흐름도.
11. **컨텍스트 주입 분석**: 토큰 수(약 450 토큰), 비용 절감(98%), 장단점(환각 원천 차단 vs 토큰 한도) 분석표.
12. **요약 캐싱 및 성능 최적화**: 60초 In-Memory TTL 캐시 및 Invalidation 전략 명시.
13. **대화 저장 동시성 및 충돌 해결**: Atomic 쓰기 및 동시성 해결 정책 정리.
14. **클라우드 시크릿 등록 가이드**: Render 및 Vercel 대시보드 환경변수 설정 단계별 매뉴얼.
15. **콜드스타트 프리워밍 전략**: Cron / UptimeRobot / GitHub Actions 14분 주기 핑 가이드.
16. **CORS 구성 및 cURL 테스트**: 도메인 등록 방법 및 Origin 헤더 검증 명령.
17. **서버측 보안 및 입력 필터링 정책**: XSS/인젝션 차단 및 Sanitize 규칙 명시.
18. **요약 기준 변경 가이드**: 로직 수정 위치 안내 및 기간 필터 단위 테스트 실행 가이드.

---

## Verification Plan

### Automated Tests
- 전체 Pytest 스위트 실행:
  ```powershell
  pytest tests/ -v
  ```
  - 기존 9개 테스트 통과 유지
  - 신규 요약 기간 필터, 캐시 무효화, 422 입력 검증 테스트 통과

### Manual Verification
1. **백엔드 API 검증**:
   - `GET /api/data/summary?start_date=2024-01-01&end_date=2024-12-31` 호출하여 기간별 요약 정상 계산 확인
   - `POST /api/data`로 음수값(`-1000`) 또는 XSS 스크립트 전송 시 422 ValidationError 반환 확인
   - 데이터 추가 후 즉시 `/api/data/summary` 호출 시 캐시 갱신 확인
2. **프론트엔드 검증**:
   - 브라우저 개발자도구 오프라인(Offline) 모드 전환 시 사용자 안내 토스트 및 에러 처리 확인
   - 모바일 뷰포트(375px, 768px)에서 반응형 레이아웃 및 사이드바 토글 동작 확인
3. **문서 검증**:
   - `README.md` 내 18개 항목의 모든 보완 요소(표, 코드 블록, 스크린샷 링크, curl 가이드)가 오탈자 없이 명확히 반영되었는지 검수
