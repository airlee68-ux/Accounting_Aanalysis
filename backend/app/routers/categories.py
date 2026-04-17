from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[schemas.CategoryOut])
def list_categories(
    type: models.TransactionType | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Category)
    if type:
        q = q.filter(models.Category.type == type)
    return q.order_by(models.Category.type, models.Category.name).all()


@router.post("", response_model=schemas.CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: schemas.CategoryCreate, db: Session = Depends(get_db)):
    exists = (
        db.query(models.Category)
        .filter(models.Category.name == payload.name, models.Category.type == payload.type)
        .first()
    )
    if exists:
        raise HTTPException(400, "Category already exists")
    obj = models.Category(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/{category_id}", response_model=schemas.CategoryOut)
def update_category(category_id: int, payload: schemas.CategoryUpdate, db: Session = Depends(get_db)):
    obj = db.get(models.Category, category_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    obj = db.get(models.Category, category_id)
    if not obj:
        raise HTTPException(404, "Category not found")
    db.delete(obj)
    db.commit()
