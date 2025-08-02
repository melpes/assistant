# 레거시 수동 테스트

이 폴더에는 실제 Google Calendar API를 사용하는 수동 테스트들이 있습니다.

## 📋 테스트 파일 목록

- **test_auth_service_legacy.py**: GoogleAuthService 수동 테스트
- **test_calendar_models_legacy.py**: CalendarEvent 모델 수동 테스트  
- **test_google_provider_manual.py**: GoogleCalendarProvider 수동 테스트
- **test_tools_integration.py**: tools.py 함수들의 통합 테스트

## 🚀 실행 방법

### 개별 실행
```bash
# 각 테스트 파일을 직접 실행
python tests/legacy/test_auth_service_legacy.py
python tests/legacy/test_calendar_models_legacy.py
python tests/legacy/test_google_provider_manual.py
python tests/legacy/test_tools_integration.py
```

### 통합 실행 (권장)
```bash
# 모든 수동 테스트 실행
python tests/run_manual_tests.py

# 인증 상태 확인 후 실행
python tests/run_manual_tests.py --check-auth

# 특정 테스트만 실행
python tests/run_manual_tests.py --test auth
python tests/run_manual_tests.py --test models
python tests/run_manual_tests.py --test provider
python tests/run_manual_tests.py --test tools
```

## ⚠️ 주의사항

1. **Google API 인증 필요**: 이 테스트들을 실행하기 전에 Google Calendar API 인증이 설정되어 있어야 합니다.

2. **실제 데이터 사용**: 이 테스트들은 실제 Google Calendar 데이터를 사용합니다.

3. **테스트 이벤트 생성**: 일부 테스트는 실제 캘린더에 테스트 이벤트를 생성할 수 있습니다. 테스트 후 수동으로 정리해주세요.

4. **API 할당량**: Google API 할당량을 소모하므로 필요할 때만 실행하세요.

## 🔧 인증 설정

1. Google Cloud Console에서 Calendar API 활성화
2. OAuth 2.0 클라이언트 ID 생성
3. `credentials.json` 파일을 프로젝트 루트에 저장
4. 첫 실행 시 브라우저에서 인증 진행

## 📊 테스트 내용

### 인증 테스트
- 인증 상태 확인
- 자격 증명 가져오기
- 토큰 만료 상태 확인

### 모델 테스트
- CalendarEvent 생성 및 변환
- Google 이벤트 형식 변환
- 데이터 검증

### Provider 테스트
- 이벤트 목록 조회
- 이벤트 생성
- 실제 API 호출 검증

### Tools 통합 테스트
- tools.py 함수들의 실제 동작 확인
- 캘린더 이벤트 조회 및 생성
- 전체 워크플로우 검증