
from sqlalchemy.orm import Session

from app.models import Part


def get_parts(db: Session):
    return db.query(Part).order_by(Part.name.asc()).all()


def get_part(db: Session, part_id: int):
    return db.query(Part).filter(Part.id == part_id).first()


def create_part(db: Session, part_data: dict):
    existing_part = db.query(Part).filter(
        Part.part_number == part_data["part_number"]
    ).first()

    if existing_part:
        raise ValueError("A part with this part number already exists.")

    part = Part(**part_data)

    try:
        db.add(part)
        db.commit()
        db.refresh(part)
        return part

    except Exception:
        db.rollback()
        raise


def update_part(db: Session, part: Part, part_data: dict):
    for field, value in part_data.items():
        setattr(part, field, value)

    try:
        db.commit()
        db.refresh(part)
        return part

    except Exception:
        db.rollback()
        raise


def get_low_stock_parts(db: Session):
    return db.query(Part).filter(
        Part.is_active.is_(True),
        Part.quantity_in_stock <= Part.reorder_level
    ).order_by(Part.quantity_in_stock.asc()).all()
