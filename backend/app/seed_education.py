"""교육용 시드 — 12개월치 가상 기업 거래 데이터 (K-IFRS).

실제 중견 제조·서비스 기업 패턴을 반영해 다양한 K-IFRS 계정과목으로 거래를 생성합니다.
- 매출구조: 제품매출(주력) + 상품매출 + 용역매출 + 영업외수익
- 매출원가: 원재료/외주가공/상품매입
- 판관비: 인건비, 임차/감가상각, 사무관리비, 광고/접대 등 25+ 계정
- 금융손익: 이자수익/이자비용/외환차손익
- 법인세비용 (분기 말 1회)

사용법:
    cd backend && python -m app.seed_education

주의:
- **기존 거래 데이터를 유지하면서 추가**합니다. 완전 초기화가 필요하면 먼저
  `python -m app.scripts.reset_transactions --yes`를 실행하세요.
- 계정과목·카테고리가 비어 있으면 기본 seed.py의 마스터 데이터도 함께 넣습니다.
"""
from __future__ import annotations

import calendar
import random
from datetime import date
from decimal import Decimal

from .database import Base, SessionLocal, engine
from . import models
from .seed import DEFAULT_ACCOUNTS, DEFAULT_CATEGORIES


# 수익 패턴: (단위 천원 — min, max)
INCOME_PATTERN = {
    "제품매출":         (8000, 25000),
    "상품매출":         (2000, 7000),
    "용역매출":         (1500, 5000),
    "이자수익":         (100, 600),
    "배당금수익":       (200, 1500),  # 분기 말에만
    "임대료수익":       (800, 1200),
    "외환차익":         (50, 400),
    "유형자산처분이익": (1000, 5000),  # 가끔
    "잡이익":           (10, 100),
}

# 매출원가 패턴
COGS_PATTERN = {
    "원재료매입":   (4000, 12000),
    "외주가공비":   (1000, 4000),
    "상품매입":     (1500, 5000),
}

# 고정비 (월 정기)
FIXED_EXPENSE_PATTERN = {
    "급여":        (8000, 12000),
    "임차료":      (1500, 2200),
    "통신비":      (80, 200),
    "수도광열비":  (200, 600),
    "보험료":      (150, 400),
    "감가상각비":  (1200, 1800),
    "지급수수료":  (300, 800),
}

# 변동비/판관비
VAR_EXPENSE_PATTERN = {
    "복리후생비":   (200, 800),
    "광고선전비":   (300, 2500),
    "접대비":       (100, 600),
    "여비교통비":   (50, 400),
    "차량유지비":   (80, 350),
    "운반비":       (100, 500),
    "수선비":       (50, 600),
    "소모품비":     (30, 250),
    "도서인쇄비":   (10, 80),
    "세금과공과":   (50, 300),
    "교육훈련비":   (100, 800),
    "연구개발비":   (500, 3000),
}

# 분기/연 단위 비용
QUARTERLY_EXPENSE = {
    "상여금":      (5000, 8000),   # 분기 말
    "퇴직급여":    (2000, 4000),   # 분기 말
    "법인세비용":  (3000, 8000),   # 분기 말 추정납부
}

# 금융 원가
FINANCE_COST = {
    "이자비용":     (300, 800),    # 매월
    "외환차손":     (50, 300),     # 가끔
    "기부금":       (100, 500),    # 가끔
}

# 월별 가중치 (성수기/비수기 — 한국 일반 제조업 패턴)
REV_WEIGHT = {1: 0.7, 2: 0.7, 3: 1.0, 4: 1.0, 5: 1.1, 6: 1.0,
              7: 0.9, 8: 0.8, 9: 1.1, 10: 1.3, 11: 1.4, 12: 1.5}
EXP_WEIGHT = {1: 1.2, 2: 1.1, 3: 1.0, 4: 1.0, 5: 1.0, 6: 1.0,
              7: 1.0, 8: 1.0, 9: 1.0, 10: 1.1, 11: 1.2, 12: 1.3}


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
    last = calendar.monthrange(y, m)[1]
    upper = min(last, max_day) if max_day else last
    return random.randint(1, max(upper, 1))


def _add_tx(db, cats, name, y, m, max_day, amount_thousand, ttype, desc=None, memo=None):
    if name not in cats:
        return 0
    db.add(models.Transaction(
        date=date(y, m, _random_day(y, m, max_day)),
        description=desc or f"{m}월 {name}",
        amount=Decimal(amount_thousand * 1000),
        type=ttype,
        category_id=cats[name].id,
        memo=memo,
    ))
    return 1


def seed_education():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _ensure_masters(db)
        cats = {c.name: c for c in db.query(models.Category).all()}

        random.seed(20260426)
        today = date.today()
        inserted = 0

        for (y, m) in _month_range(today, 12):
            rw = REV_WEIGHT[m]
            ew = EXP_WEIGHT[m]
            max_day = today.day if (y == today.year and m == today.month) else None
            is_quarter_end = m in (3, 6, 9, 12)

            # ── 매출 (제품/상품/용역) — 매월 다수 ──
            for _ in range(random.randint(4, 7)):
                lo, hi = INCOME_PATTERN["제품매출"]
                amt = int(random.randint(lo, hi) * rw)
                inserted += _add_tx(db, cats, "제품매출", y, m, max_day, amt, models.TransactionType.INCOME)
            for _ in range(random.randint(2, 4)):
                lo, hi = INCOME_PATTERN["상품매출"]
                amt = int(random.randint(lo, hi) * rw)
                inserted += _add_tx(db, cats, "상품매출", y, m, max_day, amt, models.TransactionType.INCOME)
            for _ in range(random.randint(1, 3)):
                lo, hi = INCOME_PATTERN["용역매출"]
                amt = int(random.randint(lo, hi) * rw)
                inserted += _add_tx(db, cats, "용역매출", y, m, max_day, amt, models.TransactionType.INCOME)

            # ── 영업외수익 ──
            lo, hi = INCOME_PATTERN["이자수익"]
            inserted += _add_tx(db, cats, "이자수익", y, m, max_day, random.randint(lo, hi), models.TransactionType.INCOME)
            lo, hi = INCOME_PATTERN["임대료수익"]
            inserted += _add_tx(db, cats, "임대료수익", y, m, max_day, random.randint(lo, hi), models.TransactionType.INCOME)
            if is_quarter_end:
                lo, hi = INCOME_PATTERN["배당금수익"]
                inserted += _add_tx(db, cats, "배당금수익", y, m, max_day, random.randint(lo, hi), models.TransactionType.INCOME)
            if random.random() < 0.3:
                lo, hi = INCOME_PATTERN["외환차익"]
                inserted += _add_tx(db, cats, "외환차익", y, m, max_day, random.randint(lo, hi), models.TransactionType.INCOME)
            if random.random() < 0.08:
                lo, hi = INCOME_PATTERN["유형자산처분이익"]
                inserted += _add_tx(db, cats, "유형자산처분이익", y, m, max_day, random.randint(lo, hi), models.TransactionType.INCOME, memo="처분이익")

            # ── 매출원가 ──
            for cat_name, (lo, hi) in COGS_PATTERN.items():
                for _ in range(random.randint(2, 4)):
                    amt = int(random.randint(lo, hi) * rw)  # 매출과 연동
                    inserted += _add_tx(db, cats, cat_name, y, m, max_day, amt, models.TransactionType.EXPENSE, memo="매출원가")

            # ── 고정비 (매월 1건) ──
            for cat_name, (lo, hi) in FIXED_EXPENSE_PATTERN.items():
                amt = int(random.randint(lo, hi) * ew)
                inserted += _add_tx(db, cats, cat_name, y, m, max_day, amt, models.TransactionType.EXPENSE, memo="고정비")

            # ── 변동비/판관비 (월 6~10건 랜덤) ──
            chosen = random.sample(list(VAR_EXPENSE_PATTERN.keys()), k=random.randint(6, 10))
            for cat_name in chosen:
                lo, hi = VAR_EXPENSE_PATTERN[cat_name]
                amt = int(random.randint(lo, hi) * ew)
                inserted += _add_tx(db, cats, cat_name, y, m, max_day, amt, models.TransactionType.EXPENSE)

            # ── 금융원가 ──
            lo, hi = FINANCE_COST["이자비용"]
            inserted += _add_tx(db, cats, "이자비용", y, m, max_day, random.randint(lo, hi), models.TransactionType.EXPENSE, memo="차입금이자")
            if random.random() < 0.25:
                lo, hi = FINANCE_COST["외환차손"]
                inserted += _add_tx(db, cats, "외환차손", y, m, max_day, random.randint(lo, hi), models.TransactionType.EXPENSE)
            if random.random() < 0.15:
                lo, hi = FINANCE_COST["기부금"]
                inserted += _add_tx(db, cats, "기부금", y, m, max_day, random.randint(lo, hi), models.TransactionType.EXPENSE)

            # ── 분기 말 거래 (상여금/퇴직급여/법인세) ──
            if is_quarter_end:
                for cat_name, (lo, hi) in QUARTERLY_EXPENSE.items():
                    inserted += _add_tx(
                        db, cats, cat_name, y, m, max_day,
                        random.randint(lo, hi),
                        models.TransactionType.EXPENSE,
                        memo=f"{m//3}분기 정산",
                    )

        db.commit()
        print(f"[seed_education] inserted {inserted} transactions over 12 months (~{today})")
    finally:
        db.close()


if __name__ == "__main__":
    seed_education()
