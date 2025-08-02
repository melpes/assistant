# 금융 거래 관리 시스템 LLM 에이전트 통합 설계

## 개요

이 설계 문서는 기존에 구현된 개인 금융 거래 관리 시스템을 LLM 에이전트와 통합하기 위한 tool calling 인터페이스 구현 방안을 설명합니다. 이를 통해 사용자는 자연어로 금융 데이터를 조회하고 분석할 수 있으며, 시스템은 기존 구현된 기능을 활용하여 요청을 처리합니다.

## 아키텍처

### 전체 시스템 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    LLM 에이전트 계층                         │
├─────────────────────────────────────────────────────────────┤
│  Gemini API  │  Tool Calling  │  컨텍스트 관리  │  응답 생성  │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    도구 인터페이스 계층                       │
├─────────────────────────────────────────────────────────────┤
│  거래 조회 도구  │  분석 도구  │  입력 도구  │  관리 도구     │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    기존 시스템 계층                          │
├─────────────────────────────────────────────────────────────┤
│  Repository  │  Service  │  Analyzer  │  Manager           │
└─────────────────────────────────────────────────────────────┘
                                │
┌─────────────────────────────────────────────────────────────┐
│                    데이터 계층                               │
├─────────────────────────────────────────────────────────────┤
│     SQLite DB     │  설정 파일  │  백업 파일                 │
└─────────────────────────────────────────────────────────────┘
```

### 핵심 컴포넌트

#### 1. 금융 도구 모듈 (Financial Tools Module)
- **역할**: LLM 에이전트가 호출할 수 있는 도구 함수 제공
- **구성요소**:
  - `transaction_tools.py`: 거래 조회 및 필터링 도구
  - `analysis_tools.py`: 지출/수입 분석 및 리포트 도구
  - `input_tools.py`: 수동 거래 입력 도구
  - `management_tools.py`: 데이터 관리 및 설정 도구

#### 2. 금융 에이전트 모듈 (Financial Agent Module)
- **역할**: LLM과 도구 간의 통합 및 컨텍스트 관리
- **구성요소**:
  - `financial_agent.py`: 금융 관련 에이전트 구현
  - `agent_context.py`: 대화 컨텍스트 관리
  - `response_formatter.py`: 응답 포맷팅 유틸리티

#### 3. 통합 모듈 (Integration Module)
- **역할**: 기존 시스템과 에이전트 연결
- **구성요소**:
  - `agent_integration.py`: 기존 시스템과 에이전트 통합
  - `error_handler.py`: 에이전트용 오류 처리

## 컴포넌트 및 인터페이스

### 1. 거래 조회 도구 (Transaction Tools)

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
    pass

def get_transaction_details(transaction_id: str) -> dict:
    """
    특정 거래의 상세 정보를 조회합니다.
    
    Args:
        transaction_id: 거래 ID
        
    Returns:
        dict: 거래 상세 정보
    """
    pass

def search_transactions(query: str, limit: int = 10) -> dict:
    """
    키워드로 거래를 검색합니다.
    
    Args:
        query: 검색 키워드
        limit: 반환할 최대 거래 수
        
    Returns:
        dict: 검색 결과 거래 목록
    """
    pass
```

### 2. 분석 도구 (Analysis Tools)

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
    pass

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
    pass

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
    pass

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
    pass

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
    pass
```

### 3. 입력 도구 (Input Tools)

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
    pass

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
    pass

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
    pass
```

### 4. 관리 도구 (Management Tools)

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
    pass

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
    pass

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
    pass

def get_system_status() -> dict:
    """
    시스템 상태 정보를 반환합니다.
    
    Returns:
        dict: 시스템 상태 정보
    """
    pass

def update_settings(
    settings: dict
) -> dict:
    """
    시스템 설정을 업데이트합니다.
    
    Args:
        settings: 업데이트할 설정 정보
        
    Returns:
        dict: 업데이트된 설정 정보
    """
    pass
```

### 5. 금융 에이전트 (Financial Agent)

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
    # 도구 정의
    tools_for_llm = [
        # 거래 조회 도구
        list_transactions,
        get_transaction_details,
        search_transactions,
        
        # 분석 도구
        analyze_expenses,
        analyze_income,
        compare_periods,
        analyze_trends,
        get_financial_summary,
        
        # 입력 도구
        add_expense,
        add_income,
        update_transaction,
        
        # 관리 도구
        add_classification_rule,
        backup_data,
        restore_data,
        get_system_status,
        update_settings
    ]
    
    # LLM 모델 설정 및 에이전트 실행
    model = genai.GenerativeModel(model_name=LLM_MODEL_NAME, tools=tools_for_llm)
    chat = model.start_chat(enable_automatic_function_calling=True)
    
    # 프롬프트 구성 및 응답 생성
    prompt = f"""
    당신은 개인 금융 관리 전문가입니다. 아래 컨텍스트와 사용자 요청을 바탕으로, 필요한 도구를 사용하거나 직접 답변하세요.
    
    [현재 컨텍스트]
    {json.dumps(context, ensure_ascii=False)}
    
    [사용자 요청]
    {query}
    """
    
    response = chat.send_message(prompt)
    return response.text
```

## 에러 처리

### 에러 처리 전략
1. **도구 수준 에러 처리**: 각 도구 함수 내에서 발생 가능한 예외 처리
2. **에이전트 수준 에러 처리**: 에이전트 실행 중 발생하는 예외 처리
3. **사용자 친화적 메시지**: 기술적 오류를 사용자가 이해하기 쉬운 메시지로 변환

```python
def handle_agent_error(error: Exception) -> str:
    """에이전트 오류를 사용자 친화적 메시지로 변환"""
    
    if isinstance(error, ValidationError):
        return f"입력 정보가 올바르지 않습니다: {error}"
    
    elif isinstance(error, DataIngestionError):
        return f"데이터 처리 중 문제가 발생했습니다: {error}"
    
    elif isinstance(error, ClassificationError):
        return f"거래 분류 중 문제가 발생했습니다: {error}"
    
    elif isinstance(error, AnalysisError):
        return f"데이터 분석 중 문제가 발생했습니다: {error}"
    
    elif isinstance(error, genai.types.generation_types.BlockedPromptException):
        return "죄송합니다. 요청하신 내용은 안전 정책에 따라 처리할 수 없습니다."
    
    else:
        return f"처리 중 오류가 발생했습니다: {error}"
```

## 통합 방안

### 기존 시스템과의 통합
1. **도구 함수 구현**: 기존 시스템의 기능을 호출하는 도구 함수 구현
2. **에이전트 통합**: `general_agent.py`에 금융 도구 추가
3. **컨텍스트 관리**: 사용자 컨텍스트에 금융 관련 정보 추가

### 통합 코드 예시
```python
# main.py 수정
from financial_agent import run_financial_agent

def main():
    # 기존 코드...
    
    # 금융 에이전트 또는 일반 에이전트 선택
    if "금융" in query or "지출" in query or "수입" in query or "거래" in query:
        final_response = run_financial_agent(query, user_context)
    else:
        final_response = run_general_agent(query, user_context)
    
    print("\n--- 최종 답변 ---")
    print(final_response)
```

## 테스트 전략

### 단위 테스트
- 각 도구 함수별 테스트 케이스 작성
- 다양한 입력 조건에 대한 테스트
- 예외 상황 처리 테스트

### 통합 테스트
- 에이전트와 도구 간의 통합 테스트
- 실제 사용자 쿼리 시나리오 테스트
- 에러 처리 및 복구 테스트

### 사용자 시나리오 테스트
- 다양한 금융 관련 질문에 대한 응답 테스트
- 후속 질문 및 컨텍스트 유지 테스트
- 복잡한 분석 요청 처리 테스트

## 보안 고려사항

### 데이터 보안
- 민감한 금융 정보 처리 시 보안 강화
- 사용자 인증 및 권한 검증
- 로깅 시 민감 정보 마스킹

### 입력 검증
- 모든 사용자 입력 및 LLM 출력 검증
- SQL 인젝션 방지
- 악의적 입력 필터링

## 성능 최적화

### 응답 시간 최적화
- 도구 함수 실행 시간 최적화
- 데이터베이스 쿼리 최적화
- 캐싱 전략 적용

### 메모리 사용 최적화
- 대용량 데이터 처리 시 스트리밍 활용
- 불필요한 데이터 로딩 방지
- 메모리 사용량 모니터링