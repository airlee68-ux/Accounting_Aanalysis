from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


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
    """손익계산서 — 기간 내 수입/지출을 카테고리별 집계."""
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
    total_rev = Decimal("0")
    total_exp = Decimal("0")
    for name, ttype, amount in rows:
        amt = Decimal(amount or 0)
        label = name or "(미분류)"
        if ttype == models.TransactionType.INCOME:
            revenue.append(schemas.IncomeStatementRow(category=label, amount=amt))
            total_rev += amt
        elif ttype == models.TransactionType.EXPENSE:
            expense.append(schemas.IncomeStatementRow(category=label, amount=amt))
            total_exp += amt

    revenue.sort(key=lambda r: r.amount, reverse=True)
    expense.sort(key=lambda r: r.amount, reverse=True)

    return schemas.IncomeStatement(
        period_start=start,
        period_end=end,
        revenue=revenue,
        expense=expense,
        total_revenue=total_rev,
        total_expense=total_exp,
        net_income=total_rev - total_exp,
    )


@router.get("/balance-sheet", response_model=schemas.BalanceSheet)
def balance_sheet(as_of: date | None = Query(None), db: Session = Depends(get_db)):
    """대차대조표 — 계정과목별 차변·대변 잔액을 집계.

    단식부기(Transaction)만 입력된 경우, 현금 계정 하나로 수입/지출을 누적해 간이 잔액을 구한다.
    분개(JournalEntry)가 있으면 복식부기 기반으로 정확히 집계한다.
    """
    as_of = as_of or date.today()

    # 1) 복식부기 분개 기준
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
    has_journal = False

    for _id, _code, name, atype, debit, credit in journal_rows:
        d, c = Decimal(debit or 0), Decimal(credit or 0)
        if d == 0 and c == 0:
            continue
        has_journal = True
        if atype in (models.AccountType.ASSET, models.AccountType.EXPENSE):
            balance = d - c
        else:
            balance = c - d
        row = schemas.BalanceSheetRow(account=name, type=atype, balance=balance)
        if atype == models.AccountType.ASSET:
            assets.append(row); total_a += balance
        elif atype == models.AccountType.LIABILITY:
            liabilities.append(row); total_l += balance
        elif atype == models.AccountType.EQUITY:
            equity.append(row); total_e += balance

    # 2) 분개가 없으면 단식부기 기반 간이 집계 (현금 + 이익잉여금)
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
        assets.append(schemas.BalanceSheetRow(account="현금성 자산", type=models.AccountType.ASSET, balance=cash))
        equity.append(schemas.BalanceSheetRow(account="이익잉여금", type=models.AccountType.EQUITY, balance=retained))
        total_a = cash
        total_e = retained

    return schemas.BalanceSheet(
        as_of=as_of,
        assets=assets,
        liabilities=liabilities,
        equity=equity,
        total_assets=total_a,
        total_liabilities=total_l,
        total_equity=total_e,
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
