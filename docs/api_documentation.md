# 개인 AI 비서 시스템 API 문서

## 개요

이 문서는 개인 AI 비서 시스템의 API 인터페이스를 설명합니다. 시스템은 멀티 에이전트 아키텍처를 통해 자연어 쿼리를 처리하고, 다양한 도구 함수를 호출하여 캘린더 관리, 금융 데이터 조회, 웹 검색 등의 작업을 수행합니다.

## 시스템 아키텍처

### 에이전트 구조

시스템은 다음과 같은 계층 구조로 구성됩니다:

1. **슈퍼바이저 에이전트**: 사용자 쿼리 분석 및 적절한 전문 에이전트로 라우팅
2. **전문 에이전트들**: 
   - 일반 에이전트 (캘린더, 웹 검색)
   - 금융 에이전트 (금융 데이터 관리)
3. **도구 함수들**: 각 에이전트가 사용하는 구체적인 기능 구현

### 스펙 기반 개발

모든 API는 `.kiro/specs/` 디렉토리의 스펙 문서에 따라 개발되며, 다음과 같은 상태로 관리됩니다:

- **IMPLEMENTED**: 구현 완료된 API
- **IN_PROGRESS**: 구현 진행 중인 API  
- **DRAFT**: 계획 단계의 API

## 에이전트 인터페이스

### 슈퍼바이저 에이전트 (Supervisor Agent)

```python
def route_query(query: str, context: dict) -> str:
    """
    사용자 쿼리를 분석하여 적절한 전문 에이전트로 라우팅합니다.
    
    Args:
        query: 사용자 쿼리
        context: 사용자 컨텍스트
        
    Returns:
        str: 처리 결과
    """
```

### 일반 에이전트 (General Agent)

```python
def run_general_agent(query: str, context: dict) -> str:
    """
    캘린더 관리, 웹 검색 등 일반 작업을 처리하는 에이전트를 실행합니다.
    
    Args:
        query: 사용자 쿼리
        context: 사용자 컨텍스트
        
    Returns:
        str: 에이전트 응답
    """
```

### 금융 에이전트 (Financial Agent)

```python
def run_financial_agent(query: str, context: dict) -> str:
    """
    금융 관련 쿼리를 처리하는 에이전트를 실행합니다.
    
    Args:
        query: 사용자 쿼리
        context: 사용자 컨텍스트
        
    Returns:
        str: 에이전트 응답
    """
```

## 캘린더 관리 API

### 캘린더 서비스 (IMPLEMENTED - 95% 완료)

#### 일정 조회

```python
def list_calendar_events(
    start_time: str = None,
    end_time: str = None,
    max_results: int = 10
) -> str:
    """
    지정된 기간의 캘린더 일정을 조회합니다.
    
    Args:
        start_time: 시작 시간 (ISO 8601 형식)
        end_time: 종료 시간 (ISO 8601 형식)
        max_results: 최대 결과 수
        
    Returns:
        str: 일정 목록 (사용자 친화적 형식)
    """
```

#### 일정 생성

```python
def create_google_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = None,
    location: str = None,
    attendees: list = None
) -> str:
    """
    새로운 캘린더 일정을 생성합니다.
    
    Args:
        summary: 일정 제목
        start_time: 시작 시간 (ISO 8601 형식)
        end_time: 종료 시간 (ISO 8601 형식)
        description: 일정 설명
        location: 장소
        attendees: 참석자 이메일 목록
        
    Returns:
        str: 생성 결과 메시지
    """
```

#### 캘린더 서비스 팩토리

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
    end_time="2024-01-15T15:00:00"
)
```

## 웹 검색 API

### Tavily 검색 (IMPLEMENTED)

```python
def search_web(query: str, max_results: int = 5) -> str:
    """
    Tavily API를 사용하여 웹 검색을 수행합니다.
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        
    Returns:
        str: 검색 결과 요약
    """
```

## 금융 거래 관리 API

### 거래 조회 도구 (Transaction Tools) - IMPLEMENTED (100% 완료)

#### 거래 목록 조회

```python
def list_transactions(
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    payment_method: str = None,
    min_amount: float = None,
    max_amount: float = None,
    transaction_type: str = None,
    limit: int = 10
) -> dict:
    """
    특정 조건에 맞는 거래 내역을 조회합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        category: 카테고리 필터
        payment_method: 결제 방식 필터
        min_amount: 최소 금액
        max_amount: 최대 금액
        transaction_type: 거래 유형 (expense/income)
        limit: 반환할 최대 거래 수
        
    Returns:
        dict: 거래 목록과 요약 정보
    """
```

#### 거래 상세 정보 조회

```python
def get_transaction_details(transaction_id: str) -> dict:
    """
    특정 거래의 상세 정보를 조회합니다.
    
    Args:
        transaction_id: 거래 ID
        
    Returns:
        dict: 거래 상세 정보
    """
```

#### 거래 검색

```python
def search_transactions(query: str, limit: int = 10) -> dict:
    """
    키워드로 거래를 검색합니다.
    
    Args:
        query: 검색 키워드
        limit: 반환할 최대 거래 수
        
    Returns:
        dict: 검색 결과 거래 목록
    """
```

#### 카테고리 목록 조회

```python
def get_available_categories() -> dict:
    """
    사용 가능한 카테고리 목록을 조회합니다.
    
    Returns:
        dict: 카테고리 목록
    """
```

#### 결제 방식 목록 조회

```python
def get_available_payment_methods() -> dict:
    """
    사용 가능한 결제 방식 목록을 조회합니다.
    
    Returns:
        dict: 결제 방식 목록
    """
```

#### 거래 날짜 범위 조회

```python
def get_transaction_date_range() -> dict:
    """
    거래 데이터의 날짜 범위를 조회합니다.
    
    Returns:
        dict: 최초 거래일과 최근 거래일
    """
```

### 분석 도구 (Analysis Tools)

#### 지출 분석

```python
def analyze_expenses(
    start_date: str = None,
    end_date: str = None,
    category: str = None,
    payment_method: str = None,
    group_by: str = "category"
) -> dict:
    """
    지출 분석 리포트를 생성합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        category: 특정 카테고리만 분석
        payment_method: 특정 결제 방식만 분석
        group_by: 그룹화 기준 (category/payment_method/daily/weekly/monthly)
        
    Returns:
        dict: 분석 결과와 요약 정보
    """
```

#### 수입 분석

```python
def analyze_income(
    start_date: str = None,
    end_date: str = None,
    income_type: str = None,
    group_by: str = "income_type"
) -> dict:
    """
    수입 분석 리포트를 생성합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        income_type: 특정 수입 유형만 분석
        group_by: 그룹화 기준 (income_type/daily/weekly/monthly)
        
    Returns:
        dict: 분석 결과와 요약 정보
    """
```

#### 수입 패턴 분석

```python
def analyze_income_patterns(months: int = 6) -> dict:
    """
    정기적인 수입 패턴을 분석합니다.
    
    Args:
        months: 분석할 개월 수
        
    Returns:
        dict: 수입 패턴 분석 결과
    """
```

#### 수입-지출 비교 분석

```python
def compare_income_expense(
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    수입과 지출을 비교 분석하고 순 현금 흐름을 계산합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        dict: 수입-지출 비교 분석 결과
    """
```

#### 트렌드 분석

```python
def analyze_trends(
    months: int = 6,
    transaction_type: str = "expense",
    category: str = None
) -> dict:
    """
    지출 또는 수입 트렌드를 분석합니다.
    
    Args:
        months: 분석할 개월 수
        transaction_type: 분석할 거래 유형 (expense/income)
        category: 특정 카테고리만 분석
        
    Returns:
        dict: 트렌드 분석 결과
    """
```

#### 재정 요약

```python
def get_financial_summary(
    start_date: str = None,
    end_date: str = None
) -> dict:
    """
    지정된 기간의 재정 요약 정보를 제공합니다.
    
    Args:
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        
    Returns:
        dict: 재정 요약 정보
    """
```

### 비교 분석 도구 (Comparison Tools)

#### 기간 비교

```python
def compare_periods(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> dict:
    """
    두 기간의 지출 또는 수입을 비교 분석합니다.
    
    Args:
        period1_start: 첫 번째 기간 시작 날짜 (YYYY-MM-DD)
        period1_end: 첫 번째 기간 종료 날짜 (YYYY-MM-DD)
        period2_start: 두 번째 기간 시작 날짜 (YYYY-MM-DD)
        period2_end: 두 번째 기간 종료 날짜 (YYYY-MM-DD)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        dict: 비교 분석 결과
    """
```

#### 월 비교

```python
def compare_months(
    month1: str,
    month2: str,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> dict:
    """
    두 월의 지출 또는 수입을 비교 분석합니다.
    
    Args:
        month1: 첫 번째 월 (YYYY-MM)
        month2: 두 번째 월 (YYYY-MM)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        dict: 비교 분석 결과
    """
```

#### 이전 기간과 비교

```python
def compare_with_previous_period(
    end_date: str,
    days: int = 30,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> dict:
    """
    지정된 기간과 동일한 길이의 이전 기간을 비교합니다.
    
    Args:
        end_date: 현재 기간 종료 날짜 (YYYY-MM-DD)
        days: 기간 길이 (일)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        dict: 비교 분석 결과
    """
```

#### 이전 월과 비교

```python
def compare_with_previous_month(
    month: str,
    transaction_type: str = "expense",
    group_by: str = "category"
) -> dict:
    """
    지정된 월과 이전 월을 비교합니다.
    
    Args:
        month: 현재 월 (YYYY-MM)
        transaction_type: 분석할 거래 유형 (expense/income)
        group_by: 그룹화 기준 (category/payment_method/income_type)
        
    Returns:
        dict: 비교 분석 결과
    """
```

#### 주요 변동 사항 분석

```python
def find_significant_changes(
    period1_start: str,
    period1_end: str,
    period2_start: str,
    period2_end: str,
    transaction_type: str = "expense",
    threshold: float = 0.2
) -> dict:
    """
    두 기간 사이의 주요 변동 사항을 찾아 분석합니다.
    
    Args:
        period1_start: 첫 번째 기간 시작 날짜 (YYYY-MM-DD)
        period1_end: 첫 번째 기간 종료 날짜 (YYYY-MM-DD)
        period2_start: 두 번째 기간 시작 날짜 (YYYY-MM-DD)
        period2_end: 두 번째 기간 종료 날짜 (YYYY-MM-DD)
        transaction_type: 분석할 거래 유형 (expense/income)
        threshold: 유의미한 변화로 간주할 변화율 임계값
        
    Returns:
        dict: 주요 변동 사항 분석 결과
    """
```

### 수동 거래 입력 도구 (Input Tools)

#### 지출 거래 추가

```python
def add_expense(
    date: str,
    amount: float,
    description: str,
    category: str = None,
    payment_method: str = None,
    memo: str = None
) -> dict:
    """
    새로운 지출 거래를 추가합니다.
    
    Args:
        date: 거래 날짜 (YYYY-MM-DD)
        amount: 거래 금액
        description: 거래 설명
        category: 카테고리
        payment_method: 결제 방식
        memo: 메모
        
    Returns:
        dict: 추가된 거래 정보
    """
```

#### 수입 거래 추가

```python
def add_income(
    date: str,
    amount: float,
    description: str,
    income_type: str = None,
    memo: str = None
) -> dict:
    """
    새로운 수입 거래를 추가합니다.
    
    Args:
        date: 거래 날짜 (YYYY-MM-DD)
        amount: 거래 금액
        description: 거래 설명
        income_type: 수입 유형
        memo: 메모
        
    Returns:
        dict: 추가된 거래 정보
    """
```

#### 거래 정보 업데이트

```python
def update_transaction(
    transaction_id: str,
    category: str = None,
    payment_method: str = None,
    income_type: str = None,
    memo: str = None,
    is_excluded: bool = None
) -> dict:
    """
    기존 거래 정보를 업데이트합니다.
    
    Args:
        transaction_id: 거래 ID
        category: 새 카테고리
        payment_method: 새 결제 방식
        income_type: 새 수입 유형
        memo: 새 메모
        is_excluded: 분석 제외 여부
        
    Returns:
        dict: 업데이트된 거래 정보
    """
```

#### 거래 일괄 추가

```python
def batch_add_transactions(transactions: list) -> dict:
    """
    여러 거래를 일괄 추가합니다.
    
    Args:
        transactions: 추가할 거래 목록
        
    Returns:
        dict: 추가 결과 정보
    """
```

#### 거래 템플릿 목록 조회

```python
def get_transaction_templates() -> dict:
    """
    저장된 거래 템플릿 목록을 조회합니다.
    
    Returns:
        dict: 템플릿 목록
    """
```

#### 거래 템플릿 적용

```python
def apply_transaction_template(
    template_id: str,
    date: str = None,
    amount: float = None
) -> dict:
    """
    템플릿을 사용하여 거래를 추가합니다.
    
    Args:
        template_id: 템플릿 ID
        date: 거래 날짜 (기본값: 오늘)
        amount: 거래 금액 (기본값: 템플릿 금액)
        
    Returns:
        dict: 추가된 거래 정보
    """
```

#### 거래 템플릿 저장

```python
def save_transaction_template(
    name: str,
    transaction_type: str,
    description: str,
    amount: float,
    category: str = None,
    payment_method: str = None,
    income_type: str = None
) -> dict:
    """
    새 거래 템플릿을 저장합니다.
    
    Args:
        name: 템플릿 이름
        transaction_type: 거래 유형 (expense/income)
        description: 거래 설명
        amount: 거래 금액
        category: 카테고리
        payment_method: 결제 방식
        income_type: 수입 유형
        
    Returns:
        dict: 저장된 템플릿 정보
    """
```

#### 거래 템플릿 삭제

```python
def delete_transaction_template(template_id: str) -> dict:
    """
    거래 템플릿을 삭제합니다.
    
    Args:
        template_id: 템플릿 ID
        
    Returns:
        dict: 삭제 결과 정보
    """
```

#### 자동완성 제안 조회

```python
def get_autocomplete_suggestions(
    query: str,
    field: str = "description",
    limit: int = 5
) -> dict:
    """
    거래 설명 등에 대한 자동완성 제안을 조회합니다.
    
    Args:
        query: 검색 쿼리
        field: 자동완성할 필드 (description/category/payment_method/income_type)
        limit: 반환할 최대 제안 수
        
    Returns:
        dict: 자동완성 제안 목록
    """
```

### 데이터 관리 도구 (Management Tools)

#### 분류 규칙 추가

```python
def add_classification_rule(
    rule_name: str,
    rule_type: str,
    condition_type: str,
    condition_value: str,
    target_value: str,
    priority: int = 0
) -> dict:
    """
    새로운 분류 규칙을 추가합니다.
    
    Args:
        rule_name: 규칙 이름
        rule_type: 규칙 유형 (category/payment_method/filter)
        condition_type: 조건 유형 (contains/equals/regex/amount_range)
        condition_value: 조건 값
        target_value: 분류 결과 값
        priority: 우선순위
        
    Returns:
        dict: 추가된 규칙 정보
    """
```

#### 분류 규칙 업데이트

```python
def update_classification_rule(
    rule_id: str,
    rule_name: str = None,
    condition_type: str = None,
    condition_value: str = None,
    target_value: str = None,
    priority: int = None,
    is_active: bool = None
) -> dict:
    """
    기존 분류 규칙을 업데이트합니다.
    
    Args:
        rule_id: 규칙 ID
        rule_name: 새 규칙 이름
        condition_type: 새 조건 유형
        condition_value: 새 조건 값
        target_value: 새 분류 결과 값
        priority: 새 우선순위
        is_active: 활성화 여부
        
    Returns:
        dict: 업데이트된 규칙 정보
    """
```

#### 분류 규칙 삭제

```python
def delete_classification_rule(rule_id: str) -> dict:
    """
    분류 규칙을 삭제합니다.
    
    Args:
        rule_id: 규칙 ID
        
    Returns:
        dict: 삭제 결과 정보
    """
```

#### 분류 규칙 목록 조회

```python
def get_classification_rules(rule_type: str = None) -> dict:
    """
    분류 규칙 목록을 조회합니다.
    
    Args:
        rule_type: 규칙 유형 필터 (category/payment_method/filter)
        
    Returns:
        dict: 규칙 목록
    """
```

#### 규칙 통계 조회

```python
def get_rule_stats(rule_id: str = None) -> dict:
    """
    분류 규칙 통계를 조회합니다.
    
    Args:
        rule_id: 특정 규칙 ID (없으면 전체 통계)
        
    Returns:
        dict: 규칙 통계 정보
    """
```

#### 데이터 백업

```python
def backup_data(
    backup_name: str = None,
    include_settings: bool = True
) -> dict:
    """
    데이터를 백업합니다.
    
    Args:
        backup_name: 백업 이름
        include_settings: 설정 포함 여부
        
    Returns:
        dict: 백업 결과 정보
    """
```

#### 데이터 복원

```python
def restore_data(
    backup_path: str,
    include_settings: bool = True
) -> dict:
    """
    백업에서 데이터를 복원합니다.
    
    Args:
        backup_path: 백업 파일 경로
        include_settings: 설정 복원 여부
        
    Returns:
        dict: 복원 결과 정보
    """
```

#### 백업 목록 조회

```python
def list_backups() -> dict:
    """
    백업 목록을 조회합니다.
    
    Returns:
        dict: 백업 목록
    """
```

#### 데이터 내보내기

```python
def export_data(
    format: str = "csv",
    start_date: str = None,
    end_date: str = None,
    transaction_type: str = None
) -> dict:
    """
    데이터를 내보냅니다.
    
    Args:
        format: 내보내기 형식 (csv/json/excel)
        start_date: 시작 날짜 (YYYY-MM-DD)
        end_date: 종료 날짜 (YYYY-MM-DD)
        transaction_type: 거래 유형 필터 (expense/income)
        
    Returns:
        dict: 내보내기 결과 정보
    """
```

#### 시스템 상태 조회

```python
def get_system_status() -> dict:
    """
    시스템 상태 정보를 반환합니다.
    
    Returns:
        dict: 시스템 상태 정보
    """
```

#### 설정 업데이트

```python
def update_settings(settings: dict) -> dict:
    """
    시스템 설정을 업데이트합니다.
    
    Args:
        settings: 업데이트할 설정 정보
        
    Returns:
        dict: 업데이트된 설정 정보
    """
```

#### 설정 조회

```python
def get_settings() -> dict:
    """
    시스템 설정을 조회합니다.
    
    Returns:
        dict: 설정 정보
    """
```

## 응답 포맷팅

### 응답 포맷팅 함수

```python
def format_response(result: Any) -> str:
    """
    도구 실행 결과를 사용자 친화적인 응답으로 포맷팅합니다.
    
    Args:
        result: 도구 실행 결과
        
    Returns:
        str: 포맷팅된 응답
    """
```

### 인사이트 추출 함수

```python
def extract_insights(data: Dict) -> List[str]:
    """
    데이터에서 인사이트를 추출합니다.
    
    Args:
        data: 분석 데이터
        
    Returns:
        List[str]: 추출된 인사이트 목록
    """
```

### 에러 처리 함수

```python
def handle_agent_error(error: Exception) -> str:
    """
    에이전트 오류를 사용자 친화적 메시지로 변환합니다.
    
    Args:
        error: 발생한 예외
        
    Returns:
        str: 사용자 친화적 오류 메시지
    """
```

## 예외 클래스

### ValidationError

입력 데이터 검증 오류를 나타냅니다.

### DataIngestionError

데이터 처리 중 발생하는 오류를 나타냅니다.

### ClassificationError

거래 분류 중 발생하는 오류를 나타냅니다.

### AnalysisError

데이터 분석 중 발생하는 오류를 나타냅니다.

### DatabaseError

데이터베이스 작업 중 발생하는 오류를 나타냅니다.

### ConfigError

설정 관련 오류를 나타냅니다.

### BackupError

백업 또는 복원 중 발생하는 오류를 나타냅니다.

## 이메일-캘린더 자동화 API (계획 중)

### 상태: DRAFT (0% 완료)

다음 기능들이 계획되어 있습니다:

#### 이메일 처리

```python
def process_email_for_calendar(email_id: str) -> dict:
    """
    이메일 내용을 분석하여 캘린더 일정을 생성합니다.
    
    Args:
        email_id: 처리할 이메일 ID
        
    Returns:
        dict: 생성된 일정 정보
    """
```

#### 자동화 규칙 관리

```python
def add_email_processing_rule(
    rule_name: str,
    trigger_condition: str,
    action_type: str,
    parameters: dict
) -> dict:
    """
    이메일 처리 자동화 규칙을 추가합니다.
    
    Args:
        rule_name: 규칙 이름
        trigger_condition: 트리거 조건
        action_type: 수행할 액션 유형
        parameters: 액션 매개변수
        
    Returns:
        dict: 추가된 규칙 정보
    """
```

자세한 요구사항은 `.kiro/specs/email-calendar-automation/requirements.md`를 참조하세요.

## 스펙 상태 추적

### 현재 구현 상태

- **캘린더 서비스**: IMPLEMENTED (95% 완료)
- **금융 거래 관리**: IMPLEMENTED (100% 완료)  
- **금융 에이전트 통합**: IN_PROGRESS (60% 완료)
- **이메일-캘린더 자동화**: DRAFT (0% 완료)

### 스펙 문서 위치

모든 API 스펙은 `.kiro/specs/` 디렉토리에서 관리됩니다:

- `calendar-service-refactor/`: 캘린더 서비스 관련 스펙
- `financial-agent-integration/`: 금융 에이전트 통합 스펙
- `financial-transaction-management/`: 금융 거래 관리 스펙
- `email-calendar-automation/`: 이메일-캘린더 자동화 스펙

스펙 관리에 대한 자세한 내용은 `docs/spec_management.md`를 참조하세요.