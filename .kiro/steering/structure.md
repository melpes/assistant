# 프로젝트 구조

## 루트 디렉토리

- `main.py`: `query.txt`에서 사용자 쿼리를 읽어오는 진입점
- `query.txt`: 사용자 입력 쿼리 파일
- `token.json`: 구글 캘린더 API 인증 정보
- `credentials.json`: 구글 API 서비스 계정 인증 정보
- `personal_data.db`: 지출 및 일정 데이터를 위한 SQLite 데이터베이스
- `requirements.txt`: Python 의존성 목록

## 소스 코드 (`src/`)

### 핵심 에이전트 파일
- `supervisor.py`: LangChain ReAct를 사용한 멀티 에이전트 코디네이터
- `general_agent.py`: 일반 작업을 위한 네이티브 Gemini 도구 호출
- `db_agent.py`: Python REPL을 사용한 데이터베이스 전용 에이전트

### 캘린더 서비스 모듈 (`src/calendar/`)
- `service.py`: 캘린더 서비스 계층
- `providers/google.py`: Google Calendar API 프로바이더
- `auth.py`: Google API 인증 서비스
- `models.py`: 캘린더 이벤트 데이터 모델
- `exceptions.py`: 캘린더 서비스 예외 클래스
- `factory.py`: 캘린더 서비스 팩토리
- `interfaces.py`: 캘린더 프로바이더 인터페이스
- `utils.py`: 유틸리티 함수들

### 유틸리티 모듈
- `config.py`: API 키 및 설정 상수
- `tools.py`: 도구 함수들 (캘린더, 검색 등)
- `database_setup.py`: 데이터베이스 스키마 생성 및 관리

### 데이터 수집
- `ingest_expenses.py`: 토스뱅크 카드 명세서 처리
- `check_db.py`: 데이터베이스 내용 검증

## 테스트 디렉토리 (`tests/`)
- `calendar/`: 캘린더 서비스 단위 테스트
- `legacy/`: 실제 API를 사용하는 수동 테스트
- `run_manual_tests.py`: 수동 테스트 실행 스크립트
- `pytest.ini`: pytest 설정 파일

## 데이터 디렉토리 (`data/`)
- 지출 데이터용 Excel 파일들 (토스뱅크 명세서)

## 아카이브 디렉토리 (`archive/`)
- 이전 버전의 에이전트 구현들 (참고용)

## 아키텍처 패턴

### 에이전트 유형
1. **Supervisor Agent**: 쿼리를 전문 에이전트로 라우팅
2. **General Agent**: 캘린더 및 웹 검색 작업 처리
3. **DB Agent**: 데이터베이스 쿼리 및 분석 처리

### 도구 통합
- `general_agent.py`에서 네이티브 Gemini 함수 호출
- 다른 에이전트에서 LangChain 도구 래핑
- 자동 함수 실행 활성화

### 데이터베이스 스키마
- `expenses`: 금융 거래 기록

### 캘린더 서비스 아키텍처
- **API 직접 호출**: Google Calendar API를 직접 호출하여 실시간 데이터 처리
- **모듈화 구조**: Provider 패턴을 통한 확장 가능한 아키텍처
- **의존성 주입**: Factory 패턴을 통한 설정 기반 서비스 생성
- **성능 최적화**: 서비스 객체 재사용 및 배치 처리 지원

## 파일 명명 규칙
- Python 파일은 snake_case 사용
- 데이터 파일은 한국어 파일명 지원
- 데이터베이스 파일은 프로젝트 루트에 위치
- 소스 코드는 `src/` 디렉토리에 분리