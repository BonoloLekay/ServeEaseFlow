from sqlalchemy.orm import Session

from app.models import Vehicle


def get_customer_vehicles(
    db: Session,
    customer_id: int
):
    return db.query(Vehicle).filter(
        Vehicle.customer_id == customer_id
    ).order_by(
        Vehicle.id
    ).all()


def get_customer_vehicle(
    db: Session,
    customer_id: int,
    vehicle_id: int
):
    return db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.customer_id == customer_id
    ).first()


def create_customer_vehicle(
    db: Session,
    customer_id: int,
    registration_number: str,
    vin: str | None,
    make: str,
    model: str,
    year: int,
    colour: str | None
):
    existing_vehicle = db.query(Vehicle).filter(
        Vehicle.registration_number == registration_number
    ).first()

    if existing_vehicle:
        raise ValueError(
            "A vehicle with this registration number already exists."
        )

    if vin:
        existing_vin = db.query(Vehicle).filter(
            Vehicle.vin == vin
        ).first()

        if existing_vin:
            raise ValueError(
                "A vehicle with this VIN already exists."
            )

    vehicle = Vehicle(
        customer_id=customer_id,
        registration_number=registration_number,
        vin=vin,
        make=make,
        model=model,
        year=year,
        colour=colour
    )

    try:
        db.add(vehicle)
        db.commit()
        db.refresh(vehicle)

        return vehicle

    except Exception:
        db.rollback()
        raise


def update_customer_vehicle(
    db: Session,
    vehicle: Vehicle,
    registration_number: str | None = None,
    vin: str | None = None,
    make: str | None = None,
    model: str | None = None,
    year: int | None = None,
    colour: str | None = None
):
    if registration_number is not None:
        existing_vehicle = db.query(Vehicle).filter(
            Vehicle.registration_number == registration_number,
            Vehicle.id != vehicle.id
        ).first()

        if existing_vehicle:
            raise ValueError(
                "A vehicle with this registration number already exists."
            )

        vehicle.registration_number = registration_number

    if vin is not None:
        existing_vin = db.query(Vehicle).filter(
            Vehicle.vin == vin,
            Vehicle.id != vehicle.id
        ).first()

        if existing_vin:
            raise ValueError(
                "A vehicle with this VIN already exists."
            )

        vehicle.vin = vin

    if make is not None:
        vehicle.make = make

    if model is not None:
        vehicle.model = model

    if year is not None:
        vehicle.year = year

    if colour is not None:
        vehicle.colour = colour

    try:
        db.commit()
        db.refresh(vehicle)

        return vehicle

    except Exception:
        db.rollback()
        raise


def delete_customer_vehicle(
    db: Session,
    vehicle: Vehicle
):
    try:
        db.delete(vehicle)
        db.commit()

    except Exception:
        db.rollback()
        raise