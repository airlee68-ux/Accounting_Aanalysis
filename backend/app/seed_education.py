"""교육용 시드 — 12개월치 가상 기업 거래 데이터.

기본 seed.py보다 풍부하고 현실감 있는 데이터셋을 생성해, 예비 회계사가
리포트 패턴(월별 추이·카테고리 비중·성수기/비수기 효과 등)을 관찰하는 데 적합.

사용법:
    cd backend && python -m app.seed_education

주의:
- **기존 거래 데이터를 유지하면서 추가**합니다. 완전 초기화가 필요하면 먼저
  `python -m app.scripts.reset_transactions --yes`를 실행하세요.
- 계정과목·카테고리가 비어 있으면 기본 seed.py의 마스터 데이터도 함께 넣습니다.
"""
from __future__ import annotations

import random
from datetime import date, timedelta
from decimal import Decimal

from .database import Base, SessionLocal, engine
from . import models
from .seed import DEFAULT_ACCOUNTS, DEFAULT_CATEGORIES

INCOME_PATTERN = {
    "제품매출": (2000, 8000),
    "서비스매출": (1000, 4000),
    "이자수익": (50, 300),
}
EXPENSE_PATTERN = {
    "급여": (4000, 6000),
    "임차료": (700, 900),
    "광고비": (100, 800),
    "통신비": (50, 120),
    "소모품비": (20, 150),
    "식비": (30, 200),
    "교통비": (10, 100),
}

# 월별 가중치 (성수기/비수기)
REV_WEIGHT = {1: 0.8, 2: 0.7, 3: 0.9, 4: 1.0, 5: 1.1, 6: 1.0,
              7: 0.9, 8: 0.8, 9: 1.0, 10: 1.2, 11: 1.4, 12: 1.5}
EXP_WEIGHT = {1: 1.3, 2: 1.2, 3: 1.1, 4: 1.0, 5: 1.0, 6: 1.0,
              7: 1.0, 8: 1.0, 9: 1.0, 10: 1.0, 11: 1.1, 12: 1.2}


def _ensure_masters(db):
    if db.query(models.Account).count() == 0:
        for code, name, atype in DEFAULT_ACCOUNTS:
            db.add(models.Account(code=code, name=name, type=atype))
    if db.query(models.Category).count() == 0:
        for name, ttype in DEFAULT_CATEGORIES:
            db.add(models.Category(name=name, type=ttype))
        db.commit()


def _month_range(end: date, months: int):
    y, m = end.year, end.month
    out = []
    for _ in range(months):
        out.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(reversed(out))


def _random_day(y: int, m: int, max_day: int | None):
    import calendar
    last = calendar.monthrange(y, m)[1]
    upper = min(last, max_day) if max_day else last
    return random.randint(1, max(upper, 1))


def seed_education():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_masters(db)
        cats_by_name = {c.name: c for c in db.query(models.Category).all()}

        random.seed(20260420)
        today = date.today()
        inserted = 0

        for (y, m) in _month_range(today, 12):
            rw = REV_WEIGHT[m]
            ew = EXP_WEIGHT[m]
            max_day = today.day if (y == today.year and m == today.month) else None

            # 수입 3~5건
            for _ in range(random.randint(3, 5)):
                cat_name = random.choice(list(INCOME_PATTERN.keys()))
                lo, hi = INCOME_PATTERN[cat_name]
                amt = int(random.randint(lo, hi) * rw) * 1000
                if cat_name not in cats_by_name:
                    continue
                db.add(models.Transaction(
                    date=date(y, m, _random_day(y, m, max_day)),
                    description=f"{m}월 {cat_name}",
                    amount=Decimal(amt),
                    type=models.TransactionType.INCOME,
                    category_id=cats_by_name[cat_name].id,
                ))
                inserted += 1

            # 고정비 3건 (임차료/통신비/급여)
            for cat_name in ("임차료", "통신비", "급여"):
                lo, hi = EXPENSE_PATTERN[cat_name]
                amt = int(random.randint(lo, hi) * ew) * 1000
                if cat_name not in cats_by_name:
                    continue
                db.add(models.Transaction(
                    date=date(y, m, _random_day(y, m, max_day)),
                    description=f"{m}월 {cat_name}",
                    amount=Decimal(amt),
                    type=models.TransactionType.EXPENSE,
                    category_id=cats_by_name[cat_name].id,
                    memo="고정비",
                ))
                inserted += 1

            # 변동비 5~9건
            for _ in range(random.randint(5, 9)):
                cat_name = random.choice(["광고비", "소모품비", "식비", "교통비"])
                lo, hi = EXPENSE_PATTERN[cat_name]
                amt = int(random.randint(lo, hi) * ew) * 1000
                if cat_name not in cats_by_name:
                    continue
                db.add(models.Transaction(
                    date=date(y, m, _random_day(y, m, max_day)),
                    description=f"{m}월 {cat_name}",
                    amount=Decimal(amt),
                    type=models.TransactionType.EXPENSE,
                    category_id=cats_by_name[cat_name].id,
                ))
                inserted += 1

        db.commit()
        print(f"[seed_education] inserted {inserted} transactions over 12 months (~{today})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_education()
