"""초기 데이터 시드 스크립트.

실행: `python -m app.seed`
기본 계정과목, 카테고리, 샘플 거래 내역을 생성합니다.
"""
from datetime import date, timedelta
from decimal import Decimal
import random

from .database import Base, SessionLocal, engine
from . import models


DEFAULT_ACCOUNTS = [
    # 자산
    ("1010", "현금", models.AccountType.ASSET),
    ("1020", "보통예금", models.AccountType.ASSET),
    ("1100", "매출채권", models.AccountType.ASSET),
    ("1200", "재고자산", models.AccountType.ASSET),
    # 부채
    ("2010", "매입채무", models.AccountType.LIABILITY),
    ("2100", "단기차입금", models.AccountType.LIABILITY),
    # 자본
    ("3010", "자본금", models.AccountType.EQUITY),
    ("3020", "이익잉여금", models.AccountType.EQUITY),
    # 수익
    ("4010", "매출액", models.AccountType.REVENUE),
    ("4020", "영업외수익", models.AccountType.REVENUE),
    # 비용
    ("5010", "매출원가", models.AccountType.EXPENSE),
    ("5020", "급여", models.AccountType.EXPENSE),
    ("5030", "임차료", models.AccountType.EXPENSE),
    ("5040", "광고선전비", models.AccountType.EXPENSE),
    ("5050", "통신비", models.AccountType.EXPENSE),
    ("5060", "소모품비", models.AccountType.EXPENSE),
]

DEFAULT_CATEGORIES = [
    ("제품매출", models.TransactionType.INCOME),
    ("서비스매출", models.TransactionType.INCOME),
    ("이자수익", models.TransactionType.INCOME),
    ("급여", models.TransactionType.EXPENSE),
    ("임차료", models.TransactionType.EXPENSE),
    ("광고비", models.TransactionType.EXPENSE),
    ("통신비", models.TransactionType.EXPENSE),
    ("소모품비", models.TransactionType.EXPENSE),
    ("식비", models.TransactionType.EXPENSE),
    ("교통비", models.TransactionType.EXPENSE),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 계정과목
        if db.query(models.Account).count() == 0:
            for code, name, atype in DEFAULT_ACCOUNTS:
                db.add(models.Account(code=code, name=name, type=atype))
            print(f"[seed] accounts: {len(DEFAULT_ACCOUNTS)}")

        # 카테고리
        if db.query(models.Category).count() == 0:
            for name, ttype in DEFAULT_CATEGORIES:
                db.add(models.Category(name=name, type=ttype))
            db.commit()
            print(f"[seed] categories: {len(DEFAULT_CATEGORIES)}")

        # 샘플 거래 (최근 6개월)
        if db.query(models.Transaction).count() == 0:
            categories = db.query(models.Category).all()
            income_cats = [c for c in categories if c.type == models.TransactionType.INCOME]
            expense_cats = [c for c in categories if c.type == models.TransactionType.EXPENSE]

            today = date.today()
            random.seed(42)
            count = 0
            for month_back in range(6):
                base = today.replace(day=1) - timedelta(days=month_back * 30)
                # 수입 3건
                for _ in range(3):
                    c = random.choice(income_cats)
                    db.add(models.Transaction(
                        date=base + timedelta(days=random.randint(0, 27)),
                        description=f"{c.name} 입금",
                        amount=Decimal(random.randint(500, 5000) * 1000),
                        type=models.TransactionType.INCOME,
                        category_id=c.id,
                    ))
                    count += 1
                # 지출 8건
                for _ in range(8):
                    c = random.choice(expense_cats)
                    db.add(models.Transaction(
                        date=base + timedelta(days=random.randint(0, 27)),
                        description=f"{c.name} 지출",
                        amount=Decimal(random.randint(10, 800) * 1000),
                        type=models.TransactionType.EXPENSE,
                        category_id=c.id,
                    ))
                    count += 1
            print(f"[seed] transactions: {count}")

        db.commit()
        print("[seed] done")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
