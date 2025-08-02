# 캘린더 서비스 통합 테스트 가이드

## 📋 개요

이 문서는 캘린더 서비스의 통합 테스트 실행 방법과 성능 검증 절차를 설명합니다.

## 🎯 테스트 범위

### 1. 통합 테스트 (test_integration.py)
- **실제 Google Calendar API 연동 테스트**
- **전체 CRUD 플로우 검증** (생성, 조회, 수정, 삭제)
- **에러 시나리오 처리 검증**
- **동시 작업 안정성 테스트**
- **대용량 데이터 처리 테스트**

### 2. 성능 테스트 (test_performance.py)
- **응답 시간 요구사항 검증**
  - 조회: 5초 이내 (요구사항 5.1)
  - 생성/수정/삭제: 3초 이내 (요구사항 5.2)
- **성능 벤치마크 측정**
- **동시 작업 성능 테스트**
- **대용량 시간 범위 조회 성능**

### 3. Tools 통합 테스트
- **tools.py 함수들의 실제 동작 검증**
- **기존 인터페이스 호환성 확인**

## 🚀 실행 방법

### 사전 준비

1. **Google Calendar API 설정**
   ```bash
   # 1. Google Cloud Console에서 프로젝트 생성
   # 2. Calendar API 활성화
   # 3. 서비스 계정 생성 및 키 다운로드
   # 4. credentials.json을 프로젝트 루트에 저장
   ```

2. **환경 검증**
   ```bash
   # 통합 테스트 실행 전 환경 검증
   python tests/verify_integration.py
   ```

### 통합 테스트 실행

#### 방법 1: 대화형 실행 (권장)
```bash
# 대화형 메뉴로 테스트 선택 실행
python tests/run_integration_tests.py
```

#### 방법 2: 명령행 실행
```bash
# 전체 통합 테스트
python run_tests.py --type integration

# 특정 테스트 클래스만
python -m pytest tests/calendar/test_integration.py::TestCalendarServiceIntegration -v

# 특정 테스트 함수만
python -m pytest tests/calendar/test_integration.py::TestCalendarServiceIntegration::test_full_crud_flow -v

# 성능 테스트만
python -m pytest tests/calendar/test_performance.py -m performance -v

# Tools 통합 테스트만
python -m pytest tests/calendar/test_integration.py::TestToolsIntegration -v
```

#### 방법 3: 개별 테스트 스크립트
```bash
# 레거시 수동 테스트
python tests/legacy/test_google_provider_manual.py
python tests/legacy/test_tools_integration.py
```

## 📊 성능 요구사항

| 작업 | 요구사항 | 테스트 방법 |
|------|----------|-------------|
| 이벤트 조회 | 5초 이내 | `test_list_events_performance` |
| 이벤트 생성 | 3초 이내 | `test_create_event_performance` |
| 이벤트 수정 | 3초 이내 | `test_update_event_performance` |
| 이벤트 삭제 | 3초 이내 | `test_delete_event_performance` |
| 대용량 조회 | 5초 이내 | `test_large_time_range_performance` |

## 🧪 테스트 시나리오

### 1. 기본 CRUD 플로우
```python
# 1. 이벤트 생성
created_event = service.create_new_event(test_event)

# 2. 이벤트 조회
events = service.get_events_for_period(start_time, end_time)

# 3. 이벤트 수정
updated_event = service.provider.update_event(event_id, updated_data)

# 4. 이벤트 삭제
result = service.provider.delete_event(event_id)
```

### 2. 에러 시나리오
- 존재하지 않는 이벤트 조회/수정/삭제
- 잘못된 시간 형식
- 빈 제목으로 이벤트 생성
- API 할당량 초과 처리

### 3. 성능 시나리오
- 단일/다중 작업 성능 측정
- 동시 작업 처리
- 큰 시간 범위 조회
- 연속 작업 안정성

## 📈 성능 벤치마크

통합 테스트는 다음과 같은 성능 지표를 측정합니다:

```
캘린더 서비스 성능 벤치마크
============================================================
1. 이벤트 조회 성능 테스트
   조회 시간: 1.23초 (요구사항: 5초 이내)
   조회 이벤트 수: 15개
   결과: ✅ 통과

2. 이벤트 생성 성능 테스트
   생성 시간: 0.87초 (요구사항: 3초 이내)
   결과: ✅ 통과

3. 이벤트 수정 성능 테스트
   수정 시간: 0.92초 (요구사항: 3초 이내)
   결과: ✅ 통과

4. 이벤트 삭제 성능 테스트
   삭제 시간: 0.76초 (요구사항: 3초 이내)
   결과: ✅ 통과

============================================================
전체 결과: 4/4 통과 (100.0%)
```

## 🚨 주의사항

### 실행 전 확인사항
1. **인증 파일**: `credentials.json`이 프로젝트 루트에 있는지 확인
2. **API 활성화**: Google Calendar API가 활성화되어 있는지 확인
3. **네트워크**: 안정적인 인터넷 연결 확인
4. **권한**: 서비스 계정에 캘린더 접근 권한이 있는지 확인

### 테스트 실행 시 주의사항
1. **실제 데이터**: 실제 Google Calendar에 테스트 이벤트가 생성됩니다
2. **자동 정리**: 대부분의 테스트 이벤트는 자동으로 삭제되지만, 실패 시 수동 삭제가 필요할 수 있습니다
3. **API 할당량**: 많은 테스트를 연속 실행하면 API 할당량에 도달할 수 있습니다
4. **실행 시간**: 통합 테스트는 실제 API 호출로 인해 시간이 오래 걸립니다

### 실패 시 대처방법
1. **인증 오류**: `credentials.json` 파일과 권한 설정 확인
2. **네트워크 오류**: 인터넷 연결 및 방화벽 설정 확인
3. **API 오류**: Google Cloud Console에서 API 상태 및 할당량 확인
4. **테스트 데이터**: Google Calendar에서 테스트 이벤트 수동 정리

## 🔧 문제 해결

### 일반적인 오류와 해결방법

#### 1. 인증 오류
```
❌ Google Calendar API 인증 실패
```
**해결방법:**
- `credentials.json` 파일 확인
- Google Cloud Console에서 Calendar API 활성화 확인
- 서비스 계정 권한 확인

#### 2. 모듈 없음 오류
```
❌ 다음 모듈이 설치되지 않았습니다: google.auth
```
**해결방법:**
```bash
pip install -r requirements.txt
```

#### 3. API 할당량 초과
```
❌ API 할당량 초과
```
**해결방법:**
- 잠시 대기 후 재실행
- Google Cloud Console에서 할당량 확인
- 테스트 실행 간격 조정

#### 4. 테스트 이벤트 정리 실패
```
⚠️ 정리 실패: 이벤트 abc123 수동 삭제 필요
```
**해결방법:**
- Google Calendar에서 해당 이벤트 수동 삭제
- 테스트 이벤트는 "테스트", "성능", "통합" 등의 키워드로 식별 가능

## 📝 테스트 결과 해석

### 성공적인 실행 예시
```
✅ 통합 테스트가 성공적으로 완료되었습니다!

주의사항:
- 테스트 중 생성된 일정이 있다면 Google Calendar에서 확인해주세요
- 일부 테스트 일정은 자동으로 삭제되지만, 실패 시 수동 삭제가 필요할 수 있습니다
```

### 실패 시 로그 분석
- **성능 실패**: 응답 시간이 요구사항을 초과한 경우
- **기능 실패**: API 호출이나 데이터 처리에서 오류 발생
- **환경 실패**: 인증이나 네트워크 문제

## 🎯 지속적 통합 (CI)

통합 테스트를 CI/CD 파이프라인에 포함할 때:

1. **환경 변수**: 인증 정보를 환경 변수로 설정
2. **조건부 실행**: 인증 정보가 있을 때만 실행
3. **타임아웃**: 각 테스트에 적절한 타임아웃 설정
4. **정리**: 테스트 후 생성된 데이터 자동 정리

```yaml
# GitHub Actions 예시
- name: Run Integration Tests
  if: ${{ secrets.GOOGLE_CREDENTIALS }}
  run: |
    echo '${{ secrets.GOOGLE_CREDENTIALS }}' > credentials.json
    python tests/verify_integration.py
    python run_tests.py --type integration
  env:
    GOOGLE_APPLICATION_CREDENTIALS: credentials.json
```

이 가이드를 통해 캘린더 서비스의 통합 테스트를 안전하고 효과적으로 실행할 수 있습니다.