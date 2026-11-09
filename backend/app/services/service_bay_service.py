from sqlalchemy.orm import Session

from app.models import ServiceBay


def create_service_bay(db: Session, bay_data):
    existing_bay = db.query(ServiceBay).filter(
        ServiceBay.bay_number == bay_data.bay_number
    ).first()

    if existing_bay:
        raise ValueError("Bay number is already registered.")

    try:
        new_bay = ServiceBay(
            bay_number=bay_data.bay_number,
            description=bay_data.description,
            is_active=True
        )

        db.add(new_bay)
        db.commit()
        db.refresh(new_bay)

        return new_bay

    except Exception:
        db.rollback()
        raise


def get_service_bay(db: Session, bay_id: int):
    bay = db.query(ServiceBay).filter(
        ServiceBay.id == bay_id
    ).first()

    if not bay:
        raise ValueError("Service bay not found.")

    return bay


def get_service_bays(db: Session):
    return db.query(ServiceBay).order_by(
        ServiceBay.id
    ).all()


def update_service_bay(
    db: Session,
    bay_id: int,
    bay_data
):
    bay = get_service_bay(db, bay_id)

    update_data = bay_data.model_dump(
        exclude_unset=True
    )

    if "bay_number" in update_data:
        existing_bay = db.query(ServiceBay).filter(
            ServiceBay.bay_number == update_data["bay_number"],
            ServiceBay.id != bay_id
        ).first()

        if existing_bay:
            raise ValueError("Bay number is already registered.")

    try:
        for field, value in update_data.items():
            setattr(bay, field, value)

        db.commit()
        db.refresh(bay)

        return bay

    except Exception:
        db.rollback()
        raise