# 스펙 관리 가이드

## 개요

이 문서는 프로젝트의 기능 스펙 관리 방법을 설명합니다. 모든 기능 개발은 스펙 문서를 통해 체계적으로 관리되며, 요구사항 정의부터 구현 완료까지의 전체 과정을 추적할 수 있습니다.

## 스펙 디렉토리 구조

```
.kiro/specs/
├── calendar-service-refactor/          # 캘린더 서비스 리팩토링
│   ├── requirements.md                 # 요구사항 문서
│   ├── design.md                      # 설계 문서
│   └── tasks.md                       # 작업 목록
├── email-calendar-automation/          # 이메일-캘린더 자동화
│   └── requirements.md
├── financial-agent-integration/        # 금융 에이전트 통합
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
├── financial-transaction-management/   # 금융 거래 관리
│   ├── requirements.md
│   ├── design.md
│   └── tasks.md
└── status-template.md                  # 상태 관리 템플릿
```

## 스펙 상태 관리

### 상태 헤더 방식

각 스펙 파일의 상단에 YAML 형식의 메타데이터를 포함합니다:

```markdown
---
status: IMPLEMENTED
completion: 95%
priority: HIGH
last_updated: 2025-02-08
implementation_notes: "캘린더 서비스 모듈화 완료, 테스트 및 문서화 진행 중"
dependencies: []
---
```

### 상태 값 정의

#### status (상태)
- **DRAFT**: 초안 단계 - 요구사항 정의 중
- **REVIEW**: 검토 중 - 요구사항 검토 및 승인 대기
- **APPROVED**: 승인됨 - 구현 시작 가능
- **IN_PROGRESS**: 진행 중 - 구현 진행 중
- **IMPLEMENTED**: 구현 완료 - 기능 구현 완료
- **ARCHIVED**: 보관됨 - 더 이상 활성화되지 않음

#### completion (완료율)
- 0-100% 범위의 숫자
- 전체 요구사항 대비 완료된 비율

#### priority (우선순위)
- **HIGH**: 높음 - 즉시 처리 필요
- **MEDIUM**: 보통 - 일반적인 우선순위
- **LOW**: 낮음 - 시간 여유가 있을 때 처리

#### last_updated (마지막 업데이트)
- YYYY-MM-DD 형식의 날짜
- 스펙이 마지막으로 수정된 날짜

#### implementation_notes (구현 메모)
- 현재 구현 상태에 대한 간단한 설명
- 주요 완료 사항이나 진행 중인 작업 내용

#### dependencies (의존성)
- 이 스펙이 의존하는 다른 스펙들의 목록
- 배열 형태로 스펙 디렉토리명 기재

## 스펙 작성 가이드

### 1. 새 스펙 생성

새로운 기능을 개발할 때는 다음 단계를 따릅니다:

1. `.kiro/specs/` 하위에 기능명으로 디렉토리 생성
2. `requirements.md` 파일 생성 및 요구사항 작성
3. 필요시 `design.md`, `tasks.md` 파일 추가 생성

### 2. 요구사항 문서 작성

`requirements.md` 파일은 다음 구조를 따릅니다:

```markdown
---
status: DRAFT
completion: 0%
priority: MEDIUM
last_updated: 2025-02-08
implementation_notes: "요구사항 정의 중"
dependencies: []
---

# [기능명] 요구사항 문서

## 소개
기능에 대한 전반적인 설명

## 요구사항

### 요구사항 1
**사용자 스토리:** 사용자로서, [목표]를 원합니다.

#### 승인 기준
1. WHEN [조건] THEN [결과]
2. WHEN [조건] THEN [결과]
...
```

### 3. 설계 문서 작성

복잡한 기능의 경우 `design.md` 파일을 생성하여 기술적 설계를 문서화합니다:

```markdown
---
status: DRAFT
completion: 0%
priority: MEDIUM
last_updated: 2025-02-08
implementation_notes: "설계 문서 작성 중"
dependencies: ["related-spec"]
---

# [기능명] 설계 문서

## 아키텍처 개요
## 모듈 구조
## API 설계
## 데이터베이스 스키마
## 보안 고려사항
```

### 4. 작업 목록 작성

구현 작업을 세분화하여 `tasks.md` 파일에 정리합니다:

```markdown
---
status: DRAFT
completion: 0%
priority: MEDIUM
last_updated: 2025-02-08
implementation_notes: "작업 목록 정의 중"
dependencies: ["related-spec"]
---

# [기능명] 작업 목록

## 구현 작업
- [ ] 작업 1
- [ ] 작업 2
- [x] 완료된 작업 3

## 테스트 작업
- [ ] 단위 테스트 작성
- [ ] 통합 테스트 작성

## 문서화 작업
- [ ] API 문서 업데이트
- [ ] 사용자 가이드 업데이트
```

## 스펙 상태 업데이트

### 정기적인 상태 업데이트

스펙의 상태는 다음 시점에 업데이트해야 합니다:

1. **요구사항 변경 시**: status, last_updated 업데이트
2. **구현 진행 시**: completion, implementation_notes 업데이트
3. **우선순위 변경 시**: priority 업데이트
4. **의존성 변경 시**: dependencies 업데이트

### 완료율 계산 가이드

completion 값은 다음 기준으로 계산합니다:

- **0%**: 요구사항 정의 시작
- **25%**: 요구사항 정의 완료, 설계 시작
- **50%**: 설계 완료, 구현 시작
- **75%**: 핵심 기능 구현 완료, 테스트 시작
- **90%**: 구현 및 테스트 완료, 문서화 진행
- **100%**: 모든 작업 완료

## 현재 스펙 상태 현황

### 완료된 스펙 (IMPLEMENTED)

#### 캘린더 서비스 리팩토링
- **상태**: IMPLEMENTED (95% 완료)
- **설명**: 구글 캘린더 API 직접 호출 방식으로 전환 완료
- **남은 작업**: 테스트 및 문서화 마무리

#### 금융 거래 관리
- **상태**: IMPLEMENTED (100% 완료)
- **설명**: 개인 금융 거래 데이터 관리 시스템 구현 완료

### 진행 중인 스펙 (IN_PROGRESS)

#### 금융 에이전트 통합
- **상태**: IN_PROGRESS (60% 완료)
- **설명**: LLM 에이전트와 금융 시스템 통합
- **현재 작업**: 고급 분석 기능 구현 중

### 계획된 스펙 (DRAFT)

#### 이메일-캘린더 자동화
- **상태**: DRAFT (0% 완료)
- **설명**: Gmail 이메일 기반 자동 일정 생성 시스템
- **우선순위**: HIGH

## 스펙 관리 도구

### 상태 확인 명령어

프로젝트 루트에서 다음 명령어로 전체 스펙 상태를 확인할 수 있습니다:

```bash
# 모든 스펙의 상태 요약 출력
find .kiro/specs -name "*.md" -exec grep -l "^---" {} \; | xargs grep -A 10 "^---"
```

### 스펙 템플릿 사용

새 스펙 생성 시 `.kiro/specs/status-template.md`를 참조하여 일관된 형식을 유지하세요.

## 베스트 프랙티스

### 1. 명확한 요구사항 작성
- 사용자 스토리 형식 사용
- 구체적이고 측정 가능한 승인 기준 정의
- WHEN-THEN 형식으로 조건과 결과 명시

### 2. 정기적인 상태 업데이트
- 주간 단위로 completion 및 implementation_notes 업데이트
- 중요한 마일스톤 달성 시 즉시 상태 반영

### 3. 의존성 관리
- 스펙 간 의존성을 명확히 정의
- 의존성 변경 시 관련 스펙들도 함께 업데이트

### 4. 문서 일관성 유지
- 모든 스펙 문서에 상태 헤더 포함
- 동일한 형식과 구조 사용
- 한국어로 작성하되 기술 용어는 영어 병기

## 문제 해결

### 자주 발생하는 문제

#### 스펙 상태가 오래된 경우
- 정기적인 리뷰 일정 수립
- 구현 진행 시 즉시 상태 업데이트 습관화

#### 의존성 충돌이 발생하는 경우
- 의존성 그래프 검토
- 필요시 스펙 분할 또는 병합 고려

#### 요구사항이 자주 변경되는 경우
- 변경 이력을 implementation_notes에 기록
- 주요 변경사항은 별도 문서로 관리

이 가이드를 통해 체계적이고 일관된 스펙 관리가 가능하며, 프로젝트의 진행 상황을 명확히 추적할 수 있습니다.