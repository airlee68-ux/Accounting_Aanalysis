# Accounting Analysis Web App

FastAPI + Vue 3로 구축한 회계관리 웹 애플리케이션입니다.
손익계산서, 대차대조표, 현금흐름표, 경영/원가 회계를 지원합니다.

## 프로젝트 구조

```
Accounting_Aanalysis/
├── backend/              # FastAPI + SQLAlchemy + PostgreSQL
├── frontend/             # Vue 3 + Vite + Pinia + Tailwind
├── .github/workflows/    # GitHub Actions CI/CD
└── README.md
```

## 기술 스택

### Backend
- **FastAPI** - REST API 프레임워크
- **SQLAlchemy 2.0** - ORM
- **Pydantic v2** - 데이터 검증
- **PostgreSQL** (운영) / **SQLite** (로컬)
- **Alembic** - 마이그레이션
- **Uvicorn** - ASGI 서버

### Frontend
- **Vue 3** (Composition API) + **Vite**
- **Pinia** - 상태 관리
- **Vue Router** - 라우팅
- **Axios** - HTTP 클라이언트
- **Tailwind CSS** - UI 스타일링
- **Chart.js** + **vue-chartjs** - 시각화

### Deployment
- **Render** - 백엔드 + PostgreSQL
- **Vercel** - 프론트엔드
- **GitHub Actions** - CI/CD

## 로컬 실행

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python -m app.seed             # 초기 데이터 생성 (선택)
uvicorn app.main:app --reload
```
API 문서: http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
접속: http://localhost:5173

## 배포

### 1. Render (백엔드)
1. Render 대시보드에서 새 **Web Service** 생성, GitHub 저장소 연결
2. Root Directory: `backend`
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. 환경 변수:
   - `DATABASE_URL` - Render PostgreSQL URL
   - `SECRET_KEY` - 랜덤 시크릿
   - `CORS_ORIGINS` - `https://your-app.vercel.app`

### 2. Vercel (프론트엔드)
1. Vercel에서 GitHub 저장소 import
2. Root Directory: `frontend`
3. Framework Preset: **Vite** (자동 감지)
4. 환경 변수:
   - `VITE_API_BASE_URL` - Render 백엔드 URL (예: `https://accounting-api.onrender.com`)

### 3. GitHub Actions (CI/CD)
저장소 Settings → Secrets에 등록:
- `RENDER_DEPLOY_HOOK_URL` - Render Deploy Hook URL
- `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`

`main` 브랜치 push 시 자동 배포됩니다...........

## 주요 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET/POST/PUT/DELETE | `/api/transactions` | 거래 내역 CRUD |
| GET/POST/PUT/DELETE | `/api/categories` | 카테고리 CRUD |
| GET/POST/PUT/DELETE | `/api/accounts` | 계정과목 CRUD |
| GET | `/api/reports/income-statement` | 손익계산서 |
| GET | `/api/reports/balance-sheet` | 대차대조표 |
| GET | `/api/reports/cash-flow` | 현금흐름표 |
| GET | `/api/reports/dashboard` | 대시보드 요약 |
