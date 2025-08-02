# 개인 AI 비서 시스템

강태희님을 위한 개인 AI 비서 시스템으로, 캘린더 일정 관리, 지출 추적, 지능형 질의응답 기능을 제공합니다.

## 핵심 기능

- **캘린더 관리**: 구글 캘린더 API 직접 연동을 통한 실시간 일정 조회, 생성, 수정, 삭제
- **지출 추적**: 토스뱅크 카드 명세서 데이터 자동 수집 및 분석
- **웹 검색**: Tavily 검색 API를 통한 실시간 정보 검색
- **멀티 에이전트 아키텍처**: 작업별 전문 에이전트 (일반 업무, 데이터베이스 쿼리)
- **한국어 지원**: 모든 사용자 상호작용과 응답이 한국어로 처리

## 캘린더 서비스 아키텍처

### 새로운 모듈화 구조

캘린더 서비스는 확장 가능한 모듈화 구조로 리팩토링되었습니다:

- **Service Layer** (`src/calendar/service.py`): 사용자 친화적인 비즈니스 로직 처리
- **Provider Layer** (`src/calendar/providers/`): 구체적인 캘린더 백엔드 구현
- **Auth Layer** (`src/calendar/auth.py`): Google API 인증 및 자격 증명 관리
- **Factory Pattern** (`src/calendar/factory.py`): 설정 기반 의존성 주입

### 주요 특징

1. **API 직접 호출**: DB 저장 방식에서 Google Calendar API 직접 호출로 전환
2. **실시간 데이터**: 항상 최신 캘린더 데이터 보장
3. **확장성**: 새로운 캘린더 서비스 추가 시 최소한의 코드 변경
4. **에러 복원력**: 네트워크 오류 및 API 오류에 대한 자동 재시도
5. **성능 최적화**: 서비스 객체 재사용 및 배치 처리 지원

### 사용 예시

```python
from src.calendar.factory import CalendarServiceFactory

# 캘린더 서비스 생성
calendar_service = CalendarServiceFactory.create_service()

# 일정 조회
events = calendar_service.get_events_for_period(
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# 일정 생성
new_event = calendar_service.create_new_event(
    title="중요한 회의",
    start_time="2024-01-15T14:00:00",
    end_time="2024-01-15T15:00:00",
    description="프로젝트 진행 상황 논의"
)

# 일정 수정
updated_event = calendar_service.update_event(
    event_id="event_id_here",
    title="수정된 회의",
    start_time="2024-01-15T15:00:00",
    end_time="2024-01-15T16:00:00"
)

# 일정 삭제
success = calendar_service.delete_event("event_id_here")
```

### 도구 함수 사용법

```python
from src.tools import list_calendar_events, create_google_calendar_event

# 일정 목록 조회
events_text = list_calendar_events(
    start_time="2024-01-01T00:00:00",
    end_time="2024-01-31T23:59:59"
)

# 새 일정 생성
result = create_google_calendar_event(
    summary="팀 미팅",
    start_time="2024-01-20T10:00:00",
    end_time="2024-01-20T11:00:00",
    location="회의실 A",
    description="주간 팀 미팅"
)
```

## 프로젝트 구조

```
├── src/
│   ├── calendar/                 # 캘린더 서비스 모듈
│   │   ├── __init__.py
│   │   ├── service.py           # 캘린더 서비스 계층
│   │   ├── factory.py           # 서비스 팩토리
│   │   ├── interfaces.py        # 추상 인터페이스
│   │   ├── models.py            # 데이터 모델
│   │   ├── auth.py              # Google 인증 서비스
│   │   ├── utils.py             # 유틸리티 함수
│   │   ├── exceptions.py        # 예외 클래스
│   │   └── providers/
│   │       └── google.py        # Google Calendar 프로바이더
│   ├── config.py                # 설정 및 API 키
│   ├── tools.py                 # 도구 함수들
│   ├── general_agent.py         # 일반 작업 에이전트
│   ├── database_setup.py        # 데이터베이스 설정
│   ├── ingest_expenses.py       # 지출 데이터 수집
│   └── check_db.py              # 데이터베이스 검증
├── tests/                       # 테스트 파일들
│   ├── calendar/                # 캘린더 서비스 테스트
│   └── legacy/                  # 수동 테스트
├── data/                        # 데이터 파일들
├── archive/                     # 이전 버전 보관
├── .kiro/                       # Kiro 설정 및 스펙 관리
│   ├── specs/                   # 기능 스펙 문서들
│   │   ├── calendar-service-refactor/     # 캘린더 서비스 리팩토링
│   │   ├── email-calendar-automation/     # 이메일-캘린더 자동화
│   │   ├── financial-agent-integration/   # 금융 에이전트 통합
│   │   ├── financial-transaction-management/ # 금융 거래 관리
│   │   └── status-template.md   # 스펙 상태 관리 템플릿
│   ├── steering/                # 에이전트 가이드라인
│   └── hooks/                   # 자동화 훅 설정
├── main.py                      # 진입점
├── query.txt                    # 사용자 쿼리
├── token.json                   # Google API 토큰
├── credentials.json             # Google API 인증 정보
└── personal_data.db             # SQLite 데이터베이스
```

## 캘린더 서비스 성능 최적화

### 주요 최적화 기능

1. **서비스 객체 재사용**: Google API 서비스 객체를 풀에서 관리하여 재사용
2. **배치 처리**: 여러 이벤트를 한 번에 처리하여 API 호출 최소화
3. **성능 모니터링**: 실시간 성능 통계 수집 및 분석
4. **자동 재시도**: 네트워크 오류 시 지수 백오프로 자동 재시도

### 배치 처리 기능

```python
# 여러 이벤트 배치 생성
events_data = [
    {
        'summary': '회의 1',
        'start_time': '2024-01-01T10:00:00',
        'end_time': '2024-01-01T11:00:00'
    },
    # ... 더 많은 이벤트
]
results = calendar_service.create_events_batch(events_data)

# 여러 이벤트 배치 삭제
event_ids = ['event_id_1', 'event_id_2', 'event_id_3']
results = calendar_service.delete_events_batch(event_ids)
```

### 성능 모니터링

```python
# 성능 보고서 생성
report = calendar_service.get_performance_report()
print(f"평균 응답 시간: {report['performance_stats']['list_events']['avg_time']:.4f}초")

# 성능 최적화 제안
optimization = calendar_service.optimize_performance()
for suggestion in optimization['suggestions']:
    print(f"제안: {suggestion}")
```

## 설치 및 설정

### 1. 가상환경 구축
```bash
conda create -n my-agent python=3.10
conda activate my-agent
pip install -r requirements.txt
```

### 2. 환경변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 필요한 값들을 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에서 다음 값들을 설정하세요:
- `GOOGLE_API_KEY`: Google Generative AI API 키
- `TAVILY_API_KEY`: Tavily 웹 검색 API 키
- `GOOGLE_CLIENT_ID`: Google OAuth 클라이언트 ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth 클라이언트 시크릿
- `GOOGLE_PROJECT_ID`: Google Cloud 프로젝트 ID

### 3. Google Calendar API 설정
1. [Google Cloud Console](https://console.cloud.google.com/)에서 프로젝트 생성
2. Calendar API 활성화
3. OAuth 2.0 클라이언트 ID 생성
4. 생성된 클라이언트 정보를 `.env` 파일에 설정

### 4. 데이터베이스 초기화
```bash
python src/database_setup.py
```

### 5. 실행
```bash
python main.py
```

## 문서

- **사용자 가이드**: `docs/user_manual.md` - 시스템 사용 방법
- **API 문서**: `docs/api_documentation.md` - 개발자용 API 레퍼런스
- **스펙 관리**: `docs/spec_management.md` - 기능 스펙 관리 가이드
- **설치 가이드**: `docs/installation_guide.md` - 상세 설치 방법

## 스펙 관리

### 스펙 상태 추적

프로젝트의 기능 개발은 `.kiro/specs/` 디렉토리에서 스펙 문서로 관리됩니다. 각 스펙은 다음과 같은 상태 정보를 포함합니다:

- **status**: 현재 상태 (DRAFT, REVIEW, APPROVED, IMPLEMENTED, ARCHIVED)
- **completion**: 완료율 (0-100%)
- **priority**: 우선순위 (HIGH, MEDIUM, LOW)
- **last_updated**: 마지막 업데이트 날짜
- **implementation_notes**: 구현 관련 메모
- **dependencies**: 의존성 스펙 목록

### 현재 스펙 상태

- **캘린더 서비스 리팩토링**: IMPLEMENTED (95% 완료)
- **금융 에이전트 통합**: IN_PROGRESS (60% 완료)
- **이메일-캘린더 자동화**: DRAFT (0% 완료)
- **금융 거래 관리**: IMPLEMENTED (100% 완료)

자세한 스펙 상태 관리 방법은 `.kiro/specs/status-template.md`를 참조하세요.

## 테스트 실행

### 단위 테스트
```bash
python run_tests.py
```

### 통합 테스트
```bash
python tests/run_integration_tests.py
```

### 수동 테스트 (실제 API 사용)
```bash
python tests/run_manual_tests.py
```
