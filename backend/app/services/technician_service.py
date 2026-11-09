from sqlalchemy.orm import Session, joinedload

from app.models import User, Technician, Role
from app.core.security import hash_password


def create_technician(
    db: Session,
    technician_data
):
    existing_user = db.query(User).filter(
        User.email == technician_data.email
    ).first()

    if existing_user:
        raise ValueError("Email address is already registered.")

    existing_technician = db.query(Technician).filter(
        Technician.employee_number == technician_data.employee_number
    ).first()

    if existing_technician:
        raise ValueError("Employee number is already registered.")

    technician_role = db.query(Role).filter(
        Role.name == "TECHNICIAN",
        Role.is_active.is_(True)
    ).first()

    if not technician_role:
        raise ValueError("Active TECHNICIAN role does not exist.")

    try:
        new_user = User(
            role_id=technician_role.id,
            email=technician_data.email,
            password_hash=hash_password(technician_data.password),
            first_name=technician_data.first_name,
            last_name=technician_data.last_name,
            phone_number=technician_data.phone_number
        )

        db.add(new_user)
        db.flush()

        new_technician = Technician(
            user_id=new_user.id,
            employee_number=technician_data.employee_number,
            specialization=technician_data.specialization,
            is_available=True
        )

        db.add(new_technician)

        db.commit()

        return get_technician(db, new_technician.id)

    except Exception:
        db.rollback()
        raise


def get_technician(
    db: Session,
    technician_id: int
):
    technician = db.query(Technician).options(
        joinedload(Technician.user)
    ).filter(
        Technician.id == technician_id
    ).first()

    if not technician:
        raise ValueError("Technician not found.")

    return technician


def get_technicians(db: Session):
    return db.query(Technician).options(
        joinedload(Technician.user)
    ).order_by(
        Technician.id
    ).all()


def update_technician(
    db: Session,
    technician_id: int,
    technician_data
):
    technician = get_technician(db, technician_id)

    update_data = technician_data.model_dump(
        exclude_unset=True
    )

    for field in [
        "first_name",
        "last_name",
        "phone_number"
    ]:
        if field in update_data:
            setattr(
                technician.user,
                field,
                update_data[field]
            )

    for field in [
        "specialization",
        "is_available"
    ]:
        if field in update_data:
            setattr(
                technician,
                field,
                update_data[field]
            )

    try:
        db.commit()
        return get_technician(db, technician_id)

    except Exception:
        db.rollback()
        raise