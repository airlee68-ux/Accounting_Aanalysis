from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from .models import AccountType, TransactionType


# --- Account ---
class AccountBase(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=100)
    type: AccountType
    description: Optional[str] = None


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    code: Optional[str] = None
    name: Optional[str] = None
    type: Optional[AccountType] = None
    description: Optional[str] = None


class AccountOut(AccountBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Category ---
class CategoryBase(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    type: TransactionType


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[TransactionType] = None


class CategoryOut(CategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


# --- Transaction ---
class TransactionBase(BaseModel):
    date: date
    description: str = Field(min_length=1, max_length=255)
    amount: Decimal = Field(gt=0)
    type: TransactionType
    category_id: Optional[int] = None
    memo: Optional[str] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = None
    amount: Optional[Decimal] = None
    type: Optional[TransactionType] = None
    category_id: Optional[int] = None
    memo: Optional[str] = None


class TransactionOut(TransactionBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    category: Optional[CategoryOut] = None


# --- Reports ---
class IncomeStatementRow(BaseModel):
    category: str
    amount: Decimal


class IncomeStatement(BaseModel):
    period_start: date
    period_end: date
    revenue: list[IncomeStatementRow]
    expense: list[IncomeStatementRow]
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal


class BalanceSheetRow(BaseModel):
    account: str
    type: AccountType
    balance: Decimal


class BalanceSheet(BaseModel):
    as_of: date
    assets: list[BalanceSheetRow]
    liabilities: list[BalanceSheetRow]
    equity: list[BalanceSheetRow]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal


class CashFlowRow(BaseModel):
    month: str  # YYYY-MM
    inflow: Decimal
    outflow: Decimal
    net: Decimal


class CashFlow(BaseModel):
    period_start: date
    period_end: date
    rows: list[CashFlowRow]
    total_inflow: Decimal
    total_outflow: Decimal
    net: Decimal


class MonthlyStat(BaseModel):
    month: str  # YYYY-MM
    income: Decimal
    expense: Decimal


class CategoryStat(BaseModel):
    category: str
    type: TransactionType
    amount: Decimal


class DashboardSummary(BaseModel):
    period_start: date
    period_end: date
    total_income: Decimal
    total_expense: Decimal
    net: Decimal
    monthly: list[MonthlyStat]
    by_category: list[CategoryStat]
    recent_transactions: list[TransactionOut]
