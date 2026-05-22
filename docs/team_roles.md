# 팀 역할 분담 & 협업 가이드

## 팀 구성 및 담당 영역

| 팀원 | 역할 | 브랜치 | 담당 폴더 |
|------|------|--------|----------|
| A | AI (에이전트·프롬프트) | `feat/agent` | `backend/app/agents/`, `backend/app/prompts/` |
| B | 백엔드 (API·통합) | `feat/backend` | `backend/`, `frontend/src/services/` |
| C | 데이터 (수집·전처리·분석) | `feat/data` | `data/` |
| D | 디자인 (UI/UX·발표) | `feat/design` | `design/`, `lovable/`, `presentation/` |

> 폴더 소유권이 분리되어 있어 서로 다른 브랜치에서 작업해도 머지 충돌이 거의 발생하지 않습니다.
> 유일한 충돌 지점은 B가 프론트↔백엔드를 연결하는 통합 시점입니다.

## 브랜치 전략

- `main` — 항상 동작하는 통합 브랜치
- `feat/*` — 팀원별 작업 브랜치 (위 표 참고)

## 작업 규칙 (무박 2일용)

| 항목 | 방식 |
|------|------|
| 작업 | 본인 `feat/*` 브랜치에서만 작업 |
| 머지 | `feat/*` → `main` PR 생성 후 본인 self-merge |
| 머지 빈도 | 2~3시간마다 `main`에 머지 + `main` pull |
| 커밋 | 작게 자주 push (노트북 사고 대비 백업) |
| `main` 보호 | 없음 — 속도 우선 |

## 기본 git 흐름

```bash
# 1. 최신 main 가져오기
git checkout main
git pull origin main

# 2. 내 브랜치로 이동 + main 최신 내용 반영
git checkout feat/backend
git merge main

# 3. 작업 후 커밋·푸시
git add .
git commit -m "작업 내용"
git push origin feat/backend

# 4. GitHub에서 feat/backend → main PR 생성 후 머지
```

## 디자이너(팀원 D) 참고

git CLI가 부담되면 다음 방법으로 파일 업로드 가능:

- **GitHub 웹 UI**: 저장소 페이지에서 파일 드래그 업로드 (`design/`, `lovable/prompts/`)
- **GitHub Desktop**: GUI 클라이언트 사용
- 또는 에셋을 팀원 B/C에게 전달해 대신 커밋

## 제출 체크리스트 (대회 필수 제출물)

- [ ] 기획서 PDF (HWP 양식 → PDF 변환)
- [ ] GitHub 링크: https://github.com/Mixup-Agent/shipyak
- [ ] 발표자료 PPT
- [ ] 시연영상 (유튜브 링크)
- [ ] README에 사용 기술·Upstage API 명시 (대회 규칙)
