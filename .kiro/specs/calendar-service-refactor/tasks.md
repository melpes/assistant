# 캘린더 서비스 리팩토링 구현 계획

- [x] 1. 핵심 인터페이스 및 데이터 모델 구현







  - src/calendar/ 디렉토리 생성
  - CalendarEvent 데이터 클래스 생성 (src/calendar/models.py)
  - CalendarProvider 추상 인터페이스 정의 (src/calendar/interfaces.py)
  - 기본 예외 클래스들 정의 (src/calendar/exceptions.py)
  - _요구사항: 2.1, 2.4_

- [x] 2. Google 인증 서비스 분리 및 구현









  - GoogleAuthService 클래스 생성 (src/calendar/auth.py)
  - 기존 ingest_calendar.py의 get_credentials 로직을 클래스로 이전
  - 토큰 갱신 및 재인증 로직 구현
  - 에러 처리 및 한국어 메시지 추가
  - _요구사항: 3.3, 3.4, 4.4_

- [x] 3. Google Calendar Provider 구현





  - GoogleCalendarProvider 클래스 생성 (src/calendar/providers/google.py)
  - list_events 메서드 구현 (API 직접 호출, DB 저장 제거)
  - create_event 메서드 구현
  - update_event 메서드 구현
  - delete_event 메서드 구현
  - get_event 메서드 구현
  - Google API 응답을 CalendarEvent로 변환하는 로직 구현
  - _요구사항: 1.1, 1.2, 1.3, 1.4_

- [x] 4. 에러 처리 및 재시도 로직 구현





  - 커스텀 예외 클래스들 구현 (exceptions.py 확장)
  - 재시도 데코레이터 구현 (src/calendar/utils.py)
  - 네트워크 오류 및 API 오류 처리
  - 한국어 에러 메시지 구현
  - _요구사항: 4.1, 4.2, 4.3_

- [x] 5. Calendar Service 계층 구현





  - CalendarService 클래스 생성 (src/calendar/service.py)
  - 사용자 친화적인 메서드들 구현 (get_events_for_period, create_new_event 등)
  - 응답 포맷팅 로직 구현
  - 성능 모니터링 데코레이터 추가
  - _요구사항: 2.4, 5.1, 5.2_

- [x] 6. 의존성 주입 및 팩토리 패턴 구현





  - CalendarServiceFactory 클래스 생성 (src/calendar/factory.py)
  - 설정 기반 프로바이더 선택 로직
  - config.py에 캘린더 관련 설정 추가
  - _요구사항: 2.2, 2.3_

- [x] 7. 기존 tools.py 함수들을 새 서비스로 교체





  - list_calendar_events 함수를 새 서비스 사용하도록 수정
  - create_google_calendar_event 함수를 새 서비스 사용하도록 수정
  - 기존 함수 시그니처 유지하여 호환성 보장
  - _요구사항: 1.1, 1.2_

- [x] 8. general_agent.py 업데이트





  - 새로운 캘린더 서비스를 사용하도록 수정
  - 도구 함수 목록 업데이트
  - 에러 처리 개선
  - _요구사항: 1.1, 1.2, 1.3, 1.4_

- [x] 9. DB 관련 코드 정리





  - database_setup.py에서 events 테이블 생성 코드 제거
  - ingest_calendar.py에서 DB 저장 로직 제거 (파일 자체는 삭제하고 인증 로직은 auth.py로 이전)
  - 사용하지 않는 DB 관련 import 제거
  - _요구사항: 3.1, 3.2, 3.5_

- [x] 10. 성능 최적화 구현





  - Google API 서비스 객체 재사용 로직
  - 배치 처리 메서드 구현 (선택사항)
  - 응답 시간 모니터링 추가
  - _요구사항: 5.3, 5.4_

- [x] 11. 단위 테스트 작성





  - tests/calendar/ 디렉토리 생성
  - GoogleCalendarProvider 테스트 작성
  - CalendarService 테스트 작성
  - GoogleAuthService 테스트 작성
  - Mock을 활용한 API 응답 테스트
  - _요구사항: 모든 요구사항의 검증_

- [x] 12. 통합 테스트 및 검증





  - 실제 Google Calendar API와 연동 테스트
  - 전체 플로우 테스트 (조회, 생성, 수정, 삭제)
  - 에러 시나리오 테스트
  - 성능 테스트 (응답 시간 확인)
  - _요구사항: 5.1, 5.2, 4.1, 4.2_

- [x] 13. 문서화 및 정리





  - 새로운 아키텍처에 대한 README 업데이트
  - 코드 주석 추가
  - 사용하지 않는 파일 제거 (ingest_calendar.py)
  - 스티어링 문서 업데이트 (structure.md)
  - _요구사항: 3.2, 6.1_