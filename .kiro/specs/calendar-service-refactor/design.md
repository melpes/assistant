# 캘린더 서비스 리팩토링 설계

## 개요

현재 DB 저장 방식의 캘린더 관리를 구글 캘린더 API 직접 호출 방식으로 전환하고, 향후 확장을 위한 모듈화된 아키텍처를 구현합니다. 전략 패턴과 의존성 주입을 활용하여 확장 가능한 구조를 설계합니다.

## 아키텍처

### 전체 구조
- **Service Layer**: 비즈니스 로직 처리
- **Provider Layer**: 구체적인 캘린더 백엔드 구현  
- **Auth Layer**: 인증 및 자격 증명 관리
- **Config Layer**: 설정 및 의존성 주입

## 컴포넌트 및 인터페이스

### 1. Calendar Interface (추상화 계층)

캘린더 제공자들이 구현해야 하는 공통 인터페이스를 정의합니다.

```python
from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

@dataclass
class CalendarEvent:
    id: Optional[str] = None
    summary: str = ""
    description: Optional[str] = None
    location: Optional[str] = None
    start_time: str = ""
    end_time: str = ""
    all_day: bool = False

class CalendarProvider(ABC):
    @abstractmethod
    def list_events(self, start_time: str, end_time: str) -> List[CalendarEvent]:
        pass
    
    @abstractmethod
    def create_event(self, event: CalendarEvent) -> CalendarEvent:
        pass
    
    @abstractmethod
    def update_event(self, event_id: str, event: CalendarEvent) -> CalendarEvent:
        pass
    
    @abstractmethod
    def delete_event(self, event_id: str) -> bool:
        pass
```

### 2. Google Calendar Provider

Google Calendar API를 사용하는 구체적인 구현체입니다.

### 3. Google Auth Service

Google API 인증을 담당하는 별도 서비스입니다.

### 4. Calendar Service

사용자 친화적인 인터페이스를 제공하는 서비스 계층입니다.

## 데이터 모델

### CalendarEvent 클래스
- 캘린더 이벤트의 공통 데이터 구조
- Google API 형식과의 변환 메서드 포함
- 검증 로직 포함

## 에러 처리

### 예외 계층 구조
- CalendarServiceError: 기본 예외
- AuthenticationError: 인증 오류
- APIQuotaExceededError: API 할당량 초과
- NetworkError: 네트워크 오류
- EventNotFoundError: 이벤트 없음

### 재시도 로직
- 네트워크 오류 시 지수 백오프로 재시도
- API 할당량 초과 시 적절한 대기 시간 적용

## 테스팅 전략

### 단위 테스트
- 각 Provider의 개별 메서드 테스트
- Mock을 활용한 API 응답 시뮬레이션

### 통합 테스트  
- 실제 Google Calendar API와의 연동 테스트
- 인증 플로우 테스트

## 성능 최적화

### 연결 재사용
- Google API 서비스 객체 재사용
- 인증 토큰 캐싱

### 배치 처리
- 여러 이벤트 동시 처리
- Google Batch API 활용

## 향후 확장성

### DB 캐싱 지원
- CachedCalendarProvider 구현
- 캐시 전략 설정 가능

### 다른 캘린더 서비스
- Outlook, Apple Calendar 등 추가 가능
- 동일한 인터페이스로 접근

### 설정 기반 전환
- 설정 파일로 프로바이더 선택
- 런타임 전환 지원