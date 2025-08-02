# src/config.py
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# --- API 키 설정 ---
# 환경변수에서 API 키를 가져옵니다.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# --- LLM 모델 설정 ---
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gemini-1.5-pro-latest")

# --- 경로 및 파일 이름 설정 ---
# 프로젝트의 최상위 경로를 자동으로 계산합니다.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_FILE_NAME = os.getenv("DB_FILE_NAME", "personal_data.db")
DB_PATH = os.path.join(BASE_DIR, DB_FILE_NAME)

# --- Google OAuth 설정 ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID")

# --- 캘린더 서비스 설정 ---
# 캘린더 서비스 관련 설정
CALENDAR_CONFIG = {
    # 사용할 캘린더 제공자 ("google")
    "provider": "google",
    
    # 사용할 캘린더 ID (환경변수에서 가져오거나 기본값 "primary")
    "calendar_id": os.getenv("CALENDAR_ID", "primary"),
    
    # 인증 관련 설정
    "auth": {
        # 토큰 파일 경로 (기본값: 프로젝트 루트의 token.json)
        "token_path": os.path.join(BASE_DIR, "token.json"),
        
        # 인증 정보 파일 경로 (기본값: 프로젝트 루트의 credentials.json)
        "credentials_path": os.path.join(BASE_DIR, "credentials.json"),
        
        # 요청할 권한 범위
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    }
}