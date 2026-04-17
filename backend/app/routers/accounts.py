from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("", response_model=list[schemas.AccountOut])
def list_accounts(
    type: models.AccountType | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Account)
    if type:
        q = q.filter(models.Account.type == type)
    return q.order_by(models.Account.code).all()


@router.post("", response_model=schemas.AccountOut, status_code=status.HTTP_201_CREATED)
def create_account(payload: schemas.AccountCreate, db: Session = Depends(get_db)):
    if db.query(models.Account).filter(models.Account.code == payload.code).first():
        raise HTTPException(400, f"Account code '{payload.code}' already exists")
    obj = models.Account(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("/{account_id}", response_model=schemas.AccountOut)
def get_account(account_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Account, account_id)
    if not obj:
        raise HTTPException(404, "Account not found")
    return obj


@router.put("/{account_id}", response_model=schemas.AccountOut)
def update_account(account_id: int, payload: schemas.AccountUpdate, db: Session = Depends(get_db)):
    obj = db.get(models.Account, account_id)
    if not obj:
        raise HTTPException(404, "Account not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Account, account_id)
    if not obj:
        raise HTTPException(404, "Account not found")
    db.delete(obj)
    db.commit()
