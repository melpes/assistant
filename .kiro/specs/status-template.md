# 스펙 상태 관리 템플릿

## 상태 표시 방법

### 1. 파일명 접두사 방식
- `[DRAFT]` - 초안 단계
- `[REVIEW]` - 검토 중
- `[APPROVED]` - 승인됨
- `[IMPLEMENTED]` - 구현 완료
- `[ARCHIVED]` - 보관됨

### 2. 상태 헤더 방식
각 스펙 파일 상단에 상태 정보 추가:

```markdown
---
status: IMPLEMENTED
completion: 85%
last_updated: 2025-02-08
implementation_notes: "캘린더 서비스 리팩토링 완료, 테스트 진행 중"
---
```

### 3. 체크리스트 방식
requirements.md나 tasks.md에 완료 체크리스트 추가:

```markdown
## 구현 상태
- [x] 요구사항 정의
- [x] 설계 문서 작성
- [ ] 구현 진행 중 (60%)
- [ ] 테스트 작성
- [ ] 문서화 완료
```

### 4. 디렉토리 구조 방식
```
.kiro/specs/
├── active/          # 진행 중인 스펙들
├── completed/       # 완료된 스펙들
├── archived/        # 보관된 스펙들
└── draft/          # 초안 단계 스펙들
```