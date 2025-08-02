# 보안 가이드

## 환경변수 관리

이 프로젝트는 보안을 위해 모든 민감한 정보를 환경변수로 관리합니다.

### 필수 환경변수

`.env` 파일에 다음 변수들을 설정해야 합니다:

```bash
# Google Generative AI API 키
GOOGLE_API_KEY=your_google_api_key_here

# Tavily 검색 API 키  
TAVILY_API_KEY=your_tavily_api_key_here

# Google OAuth 클라이언트 정보
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
GOOGLE_PROJECT_ID=your_google_project_id_here
```

### 보안 주의사항

1. **절대 커밋하지 마세요**: `.env` 파일은 `.gitignore`에 포함되어 있습니다.
2. **API 키 보호**: API 키를 공개 저장소에 업로드하지 마세요.
3. **권한 최소화**: Google OAuth 스코프를 필요한 최소한으로 제한하세요.
4. **정기적 갱신**: API 키를 정기적으로 갱신하세요.

### 자동 생성 파일

다음 파일들은 환경변수를 기반으로 자동 생성됩니다:
- `credentials.json`: Google OAuth 클라이언트 정보
- `token.json`: Google API 액세스 토큰 (첫 인증 후 생성)

### 개발 환경 설정

1. `.env.example`을 복사하여 `.env` 생성:
   ```bash
   cp .env.example .env
   ```

2. `.env` 파일에 실제 값 입력

3. 애플리케이션 실행:
   ```bash
   python main.py
   ```

### 배포 시 주의사항

- 프로덕션 환경에서는 환경변수를 시스템 레벨에서 설정
- `.env` 파일을 서버에 직접 업로드하지 말고 환경변수 관리 도구 사용
- 로그에 민감한 정보가 출력되지 않도록 주의