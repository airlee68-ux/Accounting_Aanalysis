from datetime import date, datetime
from decimal import Decimal
import enum

from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, Enum as SAEnum, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class AccountType(str, enum.Enum):
    ASSET = "ASSET"           # 자산
    LIABILITY = "LIABILITY"   # 부채
    EQUITY = "EQUITY"         # 자본
    REVENUE = "REVENUE"       # 수익
    EXPENSE = "EXPENSE"       # 비용


class TransactionType(str, enum.Enum):
    INCOME = "INCOME"     # 수입
    EXPENSE = "EXPENSE"   # 지출
    TRANSFER = "TRANSFER" # 대체


class Account(Base):
    """계정과목 — 손익/재무상태표 작성을 위한 마스터"""
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), index=True)
    type: Mapped[AccountType] = mapped_column(SAEnum(AccountType), index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    journal_entries: Mapped[list["JournalEntry"]] = relationship(back_populates="account")


class Category(Base):
    """지출/수입 분류 (식비, 매출, 인건비 등)"""
    __tablename__ = "categories"
    __table_args__ = (UniqueConstraint("name", "type", name="uq_category_name_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(80), index=True)
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="category")


class Transaction(Base):
    """거래 — 단순 입출금 레벨에서 기록. 복식부기 분개는 JournalEntry로 확장"""
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    description: Mapped[str] = mapped_column(String(255))
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    type: Mapped[TransactionType] = mapped_column(SAEnum(TransactionType), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    memo: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category: Mapped["Category | None"] = relationship(back_populates="transactions")
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="transaction", cascade="all, delete-orphan"
    )


class JournalEntry(Base):
    """분개 라인 — 차변(debit) / 대변(credit) 중 하나에 금액 기록 (복식부기)"""
    __tablename__ = "journal_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    debit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))
    credit: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=Decimal("0"))

    transaction: Mapped["Transaction"] = relationship(back_populates="journal_entries")
    account: Mapped["Account"] = relationship(back_populates="journal_entries")
