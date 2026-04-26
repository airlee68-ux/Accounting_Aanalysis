"""초기 데이터 시드 스크립트 (K-IFRS 기준).

실행: `python -m app.seed`
한국채택국제회계기준(K-IFRS) 재무제표 표시 체계에 따라 계정과목을 구성합니다.
- 자산: 유동/비유동 구분
- 부채: 유동/비유동 구분
- 자본: 납입자본/이익잉여금/기타포괄손익누계액
- 손익: 매출/매출원가/판관비/금융손익/법인세 구분
"""
from datetime import date, timedelta
from decimal import Decimal
import random

from .database import Base, SessionLocal, engine
from . import models


# ─────────────────────────────────────────────────────────────────────
# K-IFRS 표준 계정과목 (코드 체계: 1xxx 자산 / 2xxx 부채 / 3xxx 자본 / 4xxx 수익 / 5xxx 비용)
# ─────────────────────────────────────────────────────────────────────
DEFAULT_ACCOUNTS = [
    # ── 유동자산 (Current Assets) 11xx ──
    ("1110", "현금및현금성자산", models.AccountType.ASSET),
    ("1120", "단기금융상품", models.AccountType.ASSET),
    ("1130", "당기손익-공정가치측정금융자산", models.AccountType.ASSET),
    ("1140", "매출채권", models.AccountType.ASSET),
    ("1145", "대손충당금", models.AccountType.ASSET),
    ("1150", "미수금", models.AccountType.ASSET),
    ("1155", "미수수익", models.AccountType.ASSET),
    ("1160", "선급금", models.AccountType.ASSET),
    ("1165", "선급비용", models.AccountType.ASSET),
    ("1170", "재고자산", models.AccountType.ASSET),
    ("1175", "부가세대급금", models.AccountType.ASSET),
    # ── 비유동자산 (Non-current Assets) 12xx ──
    ("1210", "장기금융상품", models.AccountType.ASSET),
    ("1220", "기타포괄손익-공정가치측정금융자산", models.AccountType.ASSET),
    ("1230", "관계기업투자", models.AccountType.ASSET),
    ("1240", "장기대여금", models.AccountType.ASSET),
    ("1250", "보증금", models.AccountType.ASSET),
    ("1310", "토지", models.AccountType.ASSET),
    ("1320", "건물", models.AccountType.ASSET),
    ("1325", "건물감가상각누계액", models.AccountType.ASSET),
    ("1330", "기계장치", models.AccountType.ASSET),
    ("1335", "기계장치감가상각누계액", models.AccountType.ASSET),
    ("1340", "차량운반구", models.AccountType.ASSET),
    ("1345", "차량운반구감가상각누계액", models.AccountType.ASSET),
    ("1350", "비품", models.AccountType.ASSET),
    ("1355", "비품감가상각누계액", models.AccountType.ASSET),
    ("1360", "사용권자산", models.AccountType.ASSET),  # IFRS 16
    ("1365", "사용권자산감가상각누계액", models.AccountType.ASSET),
    ("1410", "영업권", models.AccountType.ASSET),
    ("1420", "산업재산권", models.AccountType.ASSET),
    ("1430", "개발비", models.AccountType.ASSET),
    ("1440", "소프트웨어", models.AccountType.ASSET),
    ("1450", "이연법인세자산", models.AccountType.ASSET),

    # ── 유동부채 (Current Liabilities) 21xx ──
    ("2110", "매입채무", models.AccountType.LIABILITY),
    ("2120", "단기차입금", models.AccountType.LIABILITY),
    ("2130", "유동성장기부채", models.AccountType.LIABILITY),
    ("2140", "미지급금", models.AccountType.LIABILITY),
    ("2145", "미지급비용", models.AccountType.LIABILITY),
    ("2150", "미지급법인세", models.AccountType.LIABILITY),
    ("2160", "선수금", models.AccountType.LIABILITY),
    ("2165", "선수수익", models.AccountType.LIABILITY),
    ("2170", "예수금", models.AccountType.LIABILITY),
    ("2175", "부가세예수금", models.AccountType.LIABILITY),
    ("2180", "유동리스부채", models.AccountType.LIABILITY),  # IFRS 16
    # ── 비유동부채 (Non-current Liabilities) 22xx ──
    ("2210", "사채", models.AccountType.LIABILITY),
    ("2220", "장기차입금", models.AccountType.LIABILITY),
    ("2230", "비유동리스부채", models.AccountType.LIABILITY),
    ("2240", "퇴직급여충당부채", models.AccountType.LIABILITY),
    ("2250", "이연법인세부채", models.AccountType.LIABILITY),
    ("2260", "장기충당부채", models.AccountType.LIABILITY),

    # ── 자본 (Equity) 3xxx ──
    ("3110", "자본금", models.AccountType.EQUITY),
    ("3120", "주식발행초과금", models.AccountType.EQUITY),
    ("3210", "이익잉여금", models.AccountType.EQUITY),
    ("3220", "법정적립금", models.AccountType.EQUITY),
    ("3310", "기타포괄손익누계액", models.AccountType.EQUITY),
    ("3320", "자기주식", models.AccountType.EQUITY),

    # ── 수익 (Revenue) 4xxx ──
    ("4110", "제품매출", models.AccountType.REVENUE),
    ("4120", "상품매출", models.AccountType.REVENUE),
    ("4130", "용역매출", models.AccountType.REVENUE),
    ("4140", "매출에누리및환입", models.AccountType.REVENUE),
    ("4210", "이자수익", models.AccountType.REVENUE),
    ("4220", "배당금수익", models.AccountType.REVENUE),
    ("4230", "외환차익", models.AccountType.REVENUE),
    ("4240", "외화환산이익", models.AccountType.REVENUE),
    ("4250", "유형자산처분이익", models.AccountType.REVENUE),
    ("4260", "잡이익", models.AccountType.REVENUE),

    # ── 비용 (Expenses) 5xxx ──
    # 매출원가
    ("5110", "제품매출원가", models.AccountType.EXPENSE),
    ("5120", "상품매출원가", models.AccountType.EXPENSE),
    # 판매비와관리비
    ("5210", "급여", models.AccountType.EXPENSE),
    ("5215", "상여금", models.AccountType.EXPENSE),
    ("5220", "퇴직급여", models.AccountType.EXPENSE),
    ("5225", "복리후생비", models.AccountType.EXPENSE),
    ("5230", "임차료", models.AccountType.EXPENSE),
    ("5235", "감가상각비", models.AccountType.EXPENSE),
    ("5240", "무형자산상각비", models.AccountType.EXPENSE),
    ("5245", "세금과공과", models.AccountType.EXPENSE),
    ("5250", "광고선전비", models.AccountType.EXPENSE),
    ("5255", "접대비", models.AccountType.EXPENSE),
    ("5260", "통신비", models.AccountType.EXPENSE),
    ("5265", "수도광열비", models.AccountType.EXPENSE),
    ("5270", "여비교통비", models.AccountType.EXPENSE),
    ("5275", "차량유지비", models.AccountType.EXPENSE),
    ("5280", "운반비", models.AccountType.EXPENSE),
    ("5285", "수선비", models.AccountType.EXPENSE),
    ("5290", "보험료", models.AccountType.EXPENSE),
    ("5295", "교육훈련비", models.AccountType.EXPENSE),
    ("5300", "도서인쇄비", models.AccountType.EXPENSE),
    ("5305", "소모품비", models.AccountType.EXPENSE),
    ("5310", "지급수수료", models.AccountType.EXPENSE),
    ("5315", "연구개발비", models.AccountType.EXPENSE),
    ("5320", "대손상각비", models.AccountType.EXPENSE),
    # 영업외비용/금융원가
    ("5410", "이자비용", models.AccountType.EXPENSE),
    ("5420", "외환차손", models.AccountType.EXPENSE),
    ("5430", "외화환산손실", models.AccountType.EXPENSE),
    ("5440", "유형자산처분손실", models.AccountType.EXPENSE),
    ("5450", "기부금", models.AccountType.EXPENSE),
    ("5460", "잡손실", models.AccountType.EXPENSE),
    # 법인세비용
    ("5510", "법인세비용", models.AccountType.EXPENSE),
]

# ─────────────────────────────────────────────────────────────────────
# 거래 카테고리 (단식부기 입력용 — 손익계산서 라벨)
# ─────────────────────────────────────────────────────────────────────
DEFAULT_CATEGORIES = [
    # 수익 (매출/영업외)
    ("제품매출", models.TransactionType.INCOME),
    ("상품매출", models.TransactionType.INCOME),
    ("용역매출", models.TransactionType.INCOME),
    ("이자수익", models.TransactionType.INCOME),
    ("배당금수익", models.TransactionType.INCOME),
    ("임대료수익", models.TransactionType.INCOME),
    ("외환차익", models.TransactionType.INCOME),
    ("유형자산처분이익", models.TransactionType.INCOME),
    ("잡이익", models.TransactionType.INCOME),
    # 매출원가
    ("원재료매입", models.TransactionType.EXPENSE),
    ("외주가공비", models.TransactionType.EXPENSE),
    ("상품매입", models.TransactionType.EXPENSE),
    # 인건비
    ("급여", models.TransactionType.EXPENSE),
    ("상여금", models.TransactionType.EXPENSE),
    ("퇴직급여", models.TransactionType.EXPENSE),
    ("복리후생비", models.TransactionType.EXPENSE),
    # 사무·관리비
    ("임차료", models.TransactionType.EXPENSE),
    ("수도광열비", models.TransactionType.EXPENSE),
    ("통신비", models.TransactionType.EXPENSE),
    ("소모품비", models.TransactionType.EXPENSE),
    ("도서인쇄비", models.TransactionType.EXPENSE),
    ("세금과공과", models.TransactionType.EXPENSE),
    ("보험료", models.TransactionType.EXPENSE),
    ("지급수수료", models.TransactionType.EXPENSE),
    # 영업활동비
    ("광고선전비", models.TransactionType.EXPENSE),
    ("접대비", models.TransactionType.EXPENSE),
    ("여비교통비", models.TransactionType.EXPENSE),
    ("운반비", models.TransactionType.EXPENSE),
    ("차량유지비", models.TransactionType.EXPENSE),
    # 자산 관련
    ("감가상각비", models.TransactionType.EXPENSE),
    ("무형자산상각비", models.TransactionType.EXPENSE),
    ("수선비", models.TransactionType.EXPENSE),
    # R&D / 교육
    ("연구개발비", models.TransactionType.EXPENSE),
    ("교육훈련비", models.TransactionType.EXPENSE),
    # 금융원가/기타
    ("이자비용", models.TransactionType.EXPENSE),
    ("외환차손", models.TransactionType.EXPENSE),
    ("기부금", models.TransactionType.EXPENSE),
    ("법인세비용", models.TransactionType.EXPENSE),
]


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(models.Account).count() == 0:
            for code, name, atype in DEFAULT_ACCOUNTS:
                db.add(models.Account(code=code, name=name, type=atype))
            print(f"[seed] accounts: {len(DEFAULT_ACCOUNTS)}")

        if db.query(models.Category).count() == 0:
            for name, ttype in DEFAULT_CATEGORIES:
                db.add(models.Category(name=name, type=ttype))
            db.commit()
            print(f"[seed] categories: {len(DEFAULT_CATEGORIES)}")

        # 샘플 거래 (최근 6개월) — 실제 기업처럼 다양한 카테고리 사용
        if db.query(models.Transaction).count() == 0:
            categories = db.query(models.Category).all()
            income_cats = [c for c in categories if c.type == models.TransactionType.INCOME]
            expense_cats = [c for c in categories if c.type == models.TransactionType.EXPENSE]

            today = date.today()
            random.seed(42)
            count = 0

            def sample_date(base_date: date) -> date:
                max_offset = 27 if base_date.month != today.month or base_date.year != today.year else max(today.day - base_date.day, 0)
                if max_offset <= 0:
                    return base_date
                return base_date + timedelta(days=random.randint(0, max_offset))

            for month_back in range(6):
                base = today.replace(day=1) - timedelta(days=month_back * 30)
                for _ in range(4):
                    c = random.choice(income_cats)
                    db.add(models.Transaction(
                        date=sample_date(base),
                        description=f"{c.name}",
                        amount=Decimal(random.randint(500, 8000) * 1000),
                        type=models.TransactionType.INCOME,
                        category_id=c.id,
                    ))
                    count += 1
                for _ in range(12):
                    c = random.choice(expense_cats)
                    db.add(models.Transaction(
                        date=sample_date(base),
                        description=f"{c.name}",
                        amount=Decimal(random.randint(10, 1500) * 1000),
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
