# src/auth_config.py
import os
import json
from .config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID, BASE_DIR

def generate_credentials_json():
    """환경변수를 기반으로 credentials.json 내용을 생성합니다."""
    if not all([GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_PROJECT_ID]):
        raise ValueError("Google OAuth 환경변수가 설정되지 않았습니다. .env 파일을 확인해주세요.")
    
    credentials_data = {
        "installed": {
            "client_id": GOOGLE_CLIENT_ID,
            "project_id": GOOGLE_PROJECT_ID,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    return credentials_data

def ensure_credentials_file():
    """credentials.json 파일이 없으면 환경변수를 기반으로 생성합니다."""
    credentials_path = os.path.join(BASE_DIR, "credentials.json")
    
    if not os.path.exists(credentials_path):
        try:
            credentials_data = generate_credentials_json()
            with open(credentials_path, 'w', encoding='utf-8') as f:
                json.dump(credentials_data, f, indent=2)
            print(f"credentials.json 파일이 생성되었습니다: {credentials_path}")
        except ValueError as e:
            print(f"경고: {e}")
            return False
    
    return True