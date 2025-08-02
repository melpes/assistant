---
inclusion: always
---

# 스펙 진행 상황 추적 가이드

## 스펙 작업 시 필수 동작

스펙 관련 작업을 수행할 때마다 다음 단계를 자동으로 수행해야 합니다:

### 1. 작업 시작 시
- 해당 스펙의 `requirements.md` 파일에서 현재 상태 확인
- 작업 시작 시간을 `last_updated` 필드에 기록
- 상태가 `DRAFT`인 경우 `IN_PROGRESS`로 변경

### 2. 작업 진행 중
- 각 태스크 완료 시 `completion` 퍼센트 업데이트
- `implementation_notes`에 현재 진행 상황 기록
- 의존성 해결 시 `dependencies` 배열에서 제거

### 3. 작업 완료 시
- 완료율이 90% 이상이면 상태를 `IMPLEMENTED`로 변경
- 최종 완료 시간을 `last_updated`에 기록
- `implementation_notes`에 완료 내용 요약

## YAML Front Matter 형식

```yaml
---
status: DRAFT|IN_PROGRESS|IMPLEMENTED|PAUSED|ARCHIVED
completion: 0-100%
priority: HIGH|MEDIUM|LOW
last_updated: YYYY-MM-DD
implementation_notes: "현재 상황에 대한 간단한 설명"
dependencies: ["의존성1", "의존성2"]
---
```

## 상태 변경 규칙

- **DRAFT → IN_PROGRESS**: 첫 번째 구현 작업 시작 시
- **IN_PROGRESS → IMPLEMENTED**: 완료율 90% 이상 달성 시
- **IN_PROGRESS → PAUSED**: 작업 일시 중단 시
- **IMPLEMENTED → ARCHIVED**: 더 이상 사용하지 않는 스펙

## 완료율 계산 가이드

### 요구사항 단계 (0-20%)
- 요구사항 문서 작성 완료: 10%
- 요구사항 검토 및 승인: 20%

### 설계 단계 (20-40%)
- 설계 문서 작성 완료: 30%
- 설계 검토 및 승인: 40%

### 구현 단계 (40-90%)
- 핵심 기능 구현: 60%
- 전체 기능 구현: 80%
- 테스트 완료: 90%

### 완료 단계 (90-100%)
- 문서화 완료: 95%
- 배포 및 검증: 100%

## 대시보드 업데이트

스펙 상태 변경 후 반드시 `.kiro/specs/README.md` 대시보드를 업데이트해야 합니다:

1. 변경된 스펙 정보를 테이블에 반영
2. 우선순위별 분류 업데이트
3. 다음 액션 아이템 목록 갱신

## 자동화 명령어

스펙 상태 업데이트 시 다음 명령어들을 활용할 수 있습니다:

```bash
# 스펙 상태 확인
python .kiro/specs/update_status.py

# 대시보드 업데이트
# (수동으로 README.md 편집 또는 스크립트 실행)
```

## 예시 워크플로우

### 새 태스크 시작 시:
1. 해당 스펙의 requirements.md 읽기
2. 현재 상태와 완료율 확인
3. 상태를 IN_PROGRESS로 변경 (필요시)
4. last_updated를 현재 날짜로 업데이트
5. implementation_notes에 시작하는 작업 내용 기록

### 태스크 완료 시:
1. 완료된 작업에 따라 completion 퍼센트 증가
2. implementation_notes 업데이트
3. 90% 이상 완료 시 status를 IMPLEMENTED로 변경
4. 대시보드(README.md) 업데이트

이 가이드를 따라 모든 스펙 관련 작업에서 일관된 진행 상황 추적을 수행하세요.