"""관리자 엔드포인트 — 운영 DB 시드/리셋 (토큰 보호).

운영(Render) DB에 K-IFRS 마스터 데이터와 대기업 규모의 거래 샘플을
한 번에 적용하기 위한 보호 엔드포인트.

사용 예시:
    curl -X POST "$API/api/admin/reseed?mode=full" \\
         -H "X-Admin-Token: $SECRET_KEY"

mode:
- "education": 거래만 새로 생성 (마스터는 비어 있을 때만 채움)
- "full": 거래·계정·카테고리 모두 삭제 후 K-IFRS 마스터 + 12개월 거래 재생성
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from .. import models
from ..config import get_settings
from ..database import get_db
from ..seed import seed
from ..seed_education import seed_education


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _verify_token(x_admin_token: str | None) -> None:
    settings = get_settings()
    expected = settings.secret_key
    if not expected or expected == "change-me":
        raise HTTPException(status_code=503, detail="SECRET_KEY 미설정")
    if not x_admin_token or x_admin_token != expected:
        raise HTTPException(status_code=401, detail="invalid admin token")


@router.post("/reseed")
def reseed(
    mode: str = Query("education", pattern="^(education|full)$"),
    x_admin_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    """K-IFRS 마스터 + 대기업 거래 샘플로 재시드.

    - mode=education: 마스터(없으면 채움) + 거래 추가
    - mode=full: 거래·계정·카테고리 전체 삭제 후 재생성 (운영 데이터 초기화 주의!)
    """
    _verify_token(x_admin_token)

    if mode == "full":
        # 의존 순서: 분개 → 거래 → 카테고리 / 계정 (Account는 JournalEntry FK)
        n_je = db.query(models.JournalEntry).delete()
        n_tx = db.query(models.Transaction).delete()
        n_cat = db.query(models.Category).delete()
        n_acc = db.query(models.Account).delete()
        db.commit()
        seed()
        seed_education()
        return {
            "status": "ok",
            "mode": "full",
            "deleted": {"journal_entries": n_je, "transactions": n_tx, "categories": n_cat, "accounts": n_acc},
        }

    # education: 마스터 보존, 거래만 추가
    seed()
    seed_education()
    return {"status": "ok", "mode": "education"}


@router.get("/stats")
def stats(
    x_admin_token: str | None = Header(None),
    db: Session = Depends(get_db),
):
    _verify_token(x_admin_token)
    return {
        "accounts": db.query(models.Account).count(),
        "categories": db.query(models.Category).count(),
        "transactions": db.query(models.Transaction).count(),
        "journal_entries": db.query(models.JournalEntry).count(),
    }
