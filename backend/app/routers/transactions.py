from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[schemas.TransactionOut])
def list_transactions(
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    type: models.TransactionType | None = None,
    category_id: int | None = None,
    limit: int = Query(200, ge=1, le=2000),
    db: Session = Depends(get_db),
):
    q = db.query(models.Transaction).options(selectinload(models.Transaction.category))
    if date_from:
        q = q.filter(models.Transaction.date >= date_from)
    if date_to:
        q = q.filter(models.Transaction.date <= date_to)
    if type:
        q = q.filter(models.Transaction.type == type)
    if category_id:
        q = q.filter(models.Transaction.category_id == category_id)
    return q.order_by(models.Transaction.date.desc(), models.Transaction.id.desc()).limit(limit).all()


@router.post("", response_model=schemas.TransactionOut, status_code=status.HTTP_201_CREATED)
def create_transaction(payload: schemas.TransactionCreate, db: Session = Depends(get_db)):
    if payload.category_id and not db.get(models.Category, payload.category_id):
        raise HTTPException(400, "Invalid category_id")
    obj = models.Transaction(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{tx_id}", response_model=schemas.TransactionOut)
def get_transaction(tx_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Transaction, tx_id)
    if not obj:
        raise HTTPException(404, "Transaction not found")
    return obj


@router.put("/{tx_id}", response_model=schemas.TransactionOut)
def update_transaction(tx_id: int, payload: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    obj = db.get(models.Transaction, tx_id)
    if not obj:
        raise HTTPException(404, "Transaction not found")
    data = payload.model_dump(exclude_unset=True)
    if "category_id" in data and data["category_id"] and not db.get(models.Category, data["category_id"]):
        raise HTTPException(400, "Invalid category_id")
    for k, v in data.items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{tx_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Transaction, tx_id)
    if not obj:
        raise HTTPException(404, "Transaction not found")
    db.delete(obj)
    db.commit()
