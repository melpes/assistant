# 기술 스택

## 핵심 기술

- **Python 3.10**: 주 프로그래밍 언어
- **Google Generative AI (Gemini)**: 에이전트 운영을 위한 메인 LLM
- **SQLite**: 개인 데이터 저장을 위한 로컬 데이터베이스
- **Pandas**: 데이터 처리 및 분석
- **Google APIs**: 캘린더 연동
- **Tavily**: 웹 검색 기능

## 주요 라이브러리

- `google-generativeai`: 네이티브 Gemini API 연동
- `tavily-python`: 웹 검색 기능
- `googleapiclient`: 구글 캘린더 API
- `pandas`: Excel/데이터 처리
- `sqlite3`: 데이터베이스 작업

## 환경 설정

```bash
# 가상환경 생성
conda create -n my-agent python=3.10
conda activate my-agent

# 의존성 설치
pip install -r requirements.txt
```

## 설정 정보

- API 키는 `src/config.py`에서 설정
- 구글 캘린더 인증 정보는 `token.json`에 저장
- 데이터베이스 경로: `personal_data.db` (프로젝트 루트)
- 기본 LLM 모델: `gemini-1.5-pro-latest`

## 주요 명령어

```bash
# 메인 애플리케이션 실행
python main.py

# 데이터베이스 설정
python src/database_setup.py

# 지출 데이터 수집
python src/ingest_expenses.py

# 캘린더 데이터 수집
python src/ingest_calendar.py

# 데이터베이스 내용 확인
python src/check_db.py
```