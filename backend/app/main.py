from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .database import Base, engine
from .routers import accounts, categories, transactions, reports, imports, admin
from . import models  # noqa: F401  -- ensure models are registered


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


settings = get_settings()

app = FastAPI(
    title="Accounting Analysis API",
    description="회계관리 웹 앱 REST API (손익/재무상태/현금흐름)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["meta"])
def root():
    return {"app": "Accounting Analysis API", "docs": "/docs"}


@app.get("/api/health", tags=["meta"])
def health():
    return {"status": "ok"}


app.include_router(accounts.router)
app.include_router(categories.router)
app.include_router(transactions.router)
app.include_router(reports.router)
app.include_router(imports.router)
app.include_router(admin.router)
