from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


# ─────────────────────────────────────────────────────────────────────
# IFRS 표시 분류 매핑
# ─────────────────────────────────────────────────────────────────────
# 손익계산서 — 카테고리/계정명 기반 기능별 분류
COGS_NAMES = {"원재료매입", "외주가공비", "상품매입", "제품매출원가", "상품매출원가"}
SGA_NAMES = {
    "급여", "상여금", "퇴직급여", "복리후생비",
    "임차료", "감가상각비", "무형자산상각비", "세금과공과",
    "광고선전비", "접대비", "통신비", "수도광열비",
    "여비교통비", "차량유지비", "운반비", "수선비",
    "보험료", "교육훈련비", "도서인쇄비", "소모품비",
    "지급수수료", "연구개발비", "대손상각비",
}
FINANCE_COST_NAMES = {"이자비용", "외환차손", "외화환산손실"}
OTHER_EXPENSE_NAMES = {"유형자산처분손실", "기부금", "잡손실"}
INCOME_TAX_NAMES = {"법인세비용"}
SALES_NAMES = {"제품매출", "상품매출", "용역매출"}
OTHER_INCOME_NAMES = {
    "이자수익", "배당금수익", "임대료수익",
    "외환차익", "외화환산이익", "유형자산처분이익", "잡이익",
}


def _classify_expense(name: str) -> str:
    if name in COGS_NAMES:
        return "cogs"
    if name in FINANCE_COST_NAMES:
        return "finance_cost"
    if name in INCOME_TAX_NAMES:
        return "income_tax"
    if name in OTHER_EXPENSE_NAMES:
        return "other_expense"
    return "sga"  # 기본 판관비


def _classify_income(name: str) -> str:
    if name in SALES_NAMES:
        return "sales"
    return "other_income"


# 재무상태표 — 코드/명 기반 유동성 구분
NON_CURRENT_ASSET_PREFIXES = ("12", "13", "14")  # 12xx 장기금융, 13xx 유형자산, 14xx 무형/이연법인세
NON_CURRENT_LIABILITY_PREFIXES = ("22",)
PAID_IN_NAMES = {"자본금", "주식발행초과금"}
RETAINED_NAMES = {"이익잉여금", "법정적립금"}


def _asset_classification(code: str) -> str:
    return "non_current" if code.startswith(NON_CURRENT_ASSET_PREFIXES) else "current"


def _liability_classification(code: str) -> str:
    return "non_current" if code.startswith(NON_CURRENT_LIABILITY_PREFIXES) else "current"


def _equity_classification(name: str) -> str:
    if name in PAID_IN_NAMES:
        return "paid_in"
    if name in RETAINED_NAMES:
        return "retained"
    return "oci"


def _default_period(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    today = date.today()
    start = date_from or today.replace(month=1, day=1)
    end = date_to or today
    return start, end


@router.get("/income-statement", response_model=schemas.IncomeStatement)
def income_statement(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """K-IFRS 기능별 손익계산서 — 기간 내 수익/비용을 카테고리별 집계 후 단계별 손익 산출."""
    start, end = _default_period(date_from, date_to)

    rows = (
        db.query(
            models.Category.name.label("name"),
            models.Transaction.type.label("type"),
            func.coalesce(func.sum(models.Transaction.amount), 0).label("amount"),
        )
        .join(models.Category, models.Transaction.category_id == models.Category.id, isouter=True)
        .filter(models.Transaction.date >= start, models.Transaction.date <= end)
        .group_by(models.Category.name, models.Transaction.type)
        .all()
    )

    revenue, expense = [], []
    sales = cogs = sga = finance_cost = income_tax = other_income = other_expense = Decimal("0")
    total_rev = Decimal("0")
    total_exp = Decimal("0")

    for name, ttype, amount in rows:
        amt = Decimal(amount or 0)
        label = name or "(미분류)"
        if ttype == models.TransactionType.INCOME:
            revenue.append(schemas.IncomeStatementRow(category=label, amount=amt))
            total_rev += amt
            if _classify_income(label) == "sales":
                sales += amt
            else:
                other_income += amt
        elif ttype == models.TransactionType.EXPENSE:
            expense.append(schemas.IncomeStatementRow(category=label, amount=amt))
            total_exp += amt
            cls = _classify_expense(label)
            if cls == "cogs":
                cogs += amt
            elif cls == "finance_cost":
                finance_cost += amt
            elif cls == "income_tax":
                income_tax += amt
            elif cls == "other_expense":
                other_expense += amt
            else:
                sga += amt

    revenue.sort(key=lambda r: r.amount, reverse=True)
    expense.sort(key=lambda r: r.amount, reverse=True)

    gross_profit = sales - cogs
    operating_profit = gross_profit - sga
    profit_before_tax = operating_profit + other_income - finance_cost - other_expense

    return schemas.IncomeStatement(
        period_start=start,
        period_end=end,
        revenue=revenue,
        expense=expense,
        total_revenue=total_rev,
        total_expense=total_exp,
        net_income=total_rev - total_exp,
        sales=sales,
        cogs=cogs,
        gross_profit=gross_profit,
        sga=sga,
        operating_profit=operating_profit,
        other_income=other_income,
        finance_cost=finance_cost,
        profit_before_tax=profit_before_tax,
        income_tax=income_tax,
    )


@router.get("/balance-sheet", response_model=schemas.BalanceSheet)
def balance_sheet(as_of: date | None = Query(None), db: Session = Depends(get_db)):
    """K-IFRS 재무상태표 — 유동/비유동 구분, 자본은 납입자본/이익잉여금/기타로 구분."""
    as_of = as_of or date.today()

    journal_rows = (
        db.query(
            models.Account.id,
            models.Account.code,
            models.Account.name,
            models.Account.type,
            func.coalesce(func.sum(models.JournalEntry.debit), 0).label("debit"),
            func.coalesce(func.sum(models.JournalEntry.credit), 0).label("credit"),
        )
        .join(models.JournalEntry, models.JournalEntry.account_id == models.Account.id, isouter=True)
        .join(
            models.Transaction,
            models.Transaction.id == models.JournalEntry.transaction_id,
            isouter=True,
        )
        .filter((models.Transaction.date <= as_of) | (models.Transaction.id.is_(None)))
        .group_by(models.Account.id, models.Account.code, models.Account.name, models.Account.type)
        .all()
    )

    assets, liabilities, equity = [], [], []
    total_a = total_l = total_e = Decimal("0")
    cur_a = nc_a = cur_l = nc_l = Decimal("0")
    has_journal = False

    for _id, code, name, atype, debit, credit in journal_rows:
        d, c = Decimal(debit or 0), Decimal(credit or 0)
        if d == 0 and c == 0:
            continue
        has_journal = True
        if atype in (models.AccountType.ASSET, models.AccountType.EXPENSE):
            balance = d - c
        else:
            balance = c - d

        if atype == models.AccountType.ASSET:
            cls = _asset_classification(code)
            assets.append(schemas.BalanceSheetRow(account=name, type=atype, balance=balance, classification=cls))
            total_a += balance
            if cls == "current":
                cur_a += balance
            else:
                nc_a += balance
        elif atype == models.AccountType.LIABILITY:
            cls = _liability_classification(code)
            liabilities.append(schemas.BalanceSheetRow(account=name, type=atype, balance=balance, classification=cls))
            total_l += balance
            if cls == "current":
                cur_l += balance
            else:
                nc_l += balance
        elif atype == models.AccountType.EQUITY:
            cls = _equity_classification(name)
            equity.append(schemas.BalanceSheetRow(account=name, type=atype, balance=balance, classification=cls))
            total_e += balance

    # 분개가 없으면 단식부기 기반 간이 집계 (현금 + 이익잉여금)
    if not has_journal:
        income_sum = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(models.Transaction.type == models.TransactionType.INCOME, models.Transaction.date <= as_of)
            .scalar()
        ) or 0
        expense_sum = (
            db.query(func.coalesce(func.sum(models.Transaction.amount), 0))
            .filter(models.Transaction.type == models.TransactionType.EXPENSE, models.Transaction.date <= as_of)
            .scalar()
        ) or 0
        cash = Decimal(income_sum) - Decimal(expense_sum)
        retained = cash
        assets.append(schemas.BalanceSheetRow(
            account="현금및현금성자산", type=models.AccountType.ASSET, balance=cash, classification="current"
        ))
        equity.append(schemas.BalanceSheetRow(
            account="이익잉여금", type=models.AccountType.EQUITY, balance=retained, classification="retained"
        ))
        total_a = cash
        cur_a = cash
        total_e = retained

    return schemas.BalanceSheet(
        as_of=as_of,
        assets=assets,
        liabilities=liabilities,
        equity=equity,
        total_assets=total_a,
        total_liabilities=total_l,
        total_equity=total_e,
        current_assets=cur_a,
        non_current_assets=nc_a,
        current_liabilities=cur_l,
        non_current_liabilities=nc_l,
    )


@router.get("/cash-flow", response_model=schemas.CashFlow)
def cash_flow(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """현금흐름표 — 월별 현금 유입/유출"""
    start, end = _default_period(date_from, date_to)

    txs = (
        db.query(models.Transaction)
        .filter(models.Transaction.date >= start, models.Transaction.date <= end)
        .all()
    )
    bucket: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"inflow": Decimal("0"), "outflow": Decimal("0")})
    for t in txs:
        key = t.date.strftime("%Y-%m")
        if t.type == models.TransactionType.INCOME:
            bucket[key]["inflow"] += t.amount
        elif t.type == models.TransactionType.EXPENSE:
            bucket[key]["outflow"] += t.amount

    rows = [
        schemas.CashFlowRow(month=m, inflow=v["inflow"], outflow=v["outflow"], net=v["inflow"] - v["outflow"])
        for m, v in sorted(bucket.items())
    ]
    total_in = sum((r.inflow for r in rows), Decimal("0"))
    total_out = sum((r.outflow for r in rows), Decimal("0"))

    return schemas.CashFlow(
        period_start=start,
        period_end=end,
        rows=rows,
        total_inflow=total_in,
        total_outflow=total_out,
        net=total_in - total_out,
    )


@router.get("/dashboard", response_model=schemas.DashboardSummary)
def dashboard(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    db: Session = Depends(get_db),
):
    """대시보드 요약 — 총수입/총지출, 월별 추이, 카테고리별 집계, 최근 거래"""
    start, end = _default_period(date_from, date_to)

    txs = (
        db.query(models.Transaction)
        .options(selectinload(models.Transaction.category))
        .filter(models.Transaction.date >= start, models.Transaction.date <= end)
        .all()
    )

    total_income = sum((t.amount for t in txs if t.type == models.TransactionType.INCOME), Decimal("0"))
    total_expense = sum((t.amount for t in txs if t.type == models.TransactionType.EXPENSE), Decimal("0"))

    # 월별
    monthly_bucket: dict[str, dict[str, Decimal]] = defaultdict(
        lambda: {"income": Decimal("0"), "expense": Decimal("0")}
    )
    for t in txs:
        key = t.date.strftime("%Y-%m")
        if t.type == models.TransactionType.INCOME:
            monthly_bucket[key]["income"] += t.amount
        elif t.type == models.TransactionType.EXPENSE:
            monthly_bucket[key]["expense"] += t.amount
    monthly = [
        schemas.MonthlyStat(month=m, income=v["income"], expense=v["expense"])
        for m, v in sorted(monthly_bucket.items())
    ]

    # 카테고리별
    cat_bucket: dict[tuple[str, models.TransactionType], Decimal] = defaultdict(lambda: Decimal("0"))
    for t in txs:
        label = t.category.name if t.category else "(미분류)"
        cat_bucket[(label, t.type)] += t.amount
    by_category = [
        schemas.CategoryStat(category=n, type=ty, amount=amt)
        for (n, ty), amt in sorted(cat_bucket.items(), key=lambda x: x[1], reverse=True)
    ]

    recent = (
        db.query(models.Transaction)
        .options(selectinload(models.Transaction.category))
        .order_by(models.Transaction.date.desc(), models.Transaction.id.desc())
        .limit(10)
        .all()
    )

    return schemas.DashboardSummary(
        period_start=start,
        period_end=end,
        total_income=total_income,
        total_expense=total_expense,
        net=total_income - total_expense,
        monthly=monthly,
        by_category=by_category,
        recent_transactions=recent,
    )
