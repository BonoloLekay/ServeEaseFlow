from app.db.session import SessionLocal
from app.models import Role


DEFAULT_ROLES = [
    {
        "name": "CUSTOMER",
        "description": "Customer portal access"
    },
    {
        "name": "ADMIN",
        "description": "Full dealership administration"
    },
    {
        "name": "RECEPTION",
        "description": "Reception and booking management"
    },
    {
        "name": "TECHNICIAN",
        "description": "Workshop and repair job management"
    },
    {
        "name": "OWNER",
        "description": "Business performance and reporting"
    }
]


def seed_roles():
    db = SessionLocal()

    try:
        for role_data in DEFAULT_ROLES:
            existing_role = db.query(Role).filter_by(
                name=role_data["name"]
            ).first()

            if not existing_role:
                db.add(Role(**role_data))

        db.commit()
        print("ServeEaseFlow roles seeded successfully!")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_roles()

    