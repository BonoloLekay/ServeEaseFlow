
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.dependencies import require_roles
from app.models import User
from app.schemas.job_assignment import (
    JobAssignmentCreate,
    JobAssignmentStatusUpdate,
    JobAssignmentResponse
)
from app.services.job_assignment_service import (
    create_job_assignment,
    get_job_assignment,
    get_job_assignments,
    update_job_assignment_status
)


router = APIRouter(
    prefix="/job-assignments",
    tags=["Job Assignments"]
)


@router.post(
    "/",
    response_model=JobAssignmentResponse,
    status_code=status.HTTP_201_CREATED
)
def create_job_assignment_endpoint(
    assignment_data: JobAssignmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN", "RECEPTION")
    )
):
    try:
        return create_job_assignment(
            db=db,
            job_card_id=assignment_data.job_card_id,
            technician_id=assignment_data.technician_id,
            service_bay_id=assignment_data.service_bay_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )


@router.get(
    "/",
    response_model=list[JobAssignmentResponse]
)
def list_job_assignments_endpoint(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "ADMIN",
            "RECEPTION",
            "TECHNICIAN",
            "OWNER"
        )
    )
):
    return get_job_assignments(db)


@router.get(
    "/{assignment_id}",
    response_model=JobAssignmentResponse
)
def get_job_assignment_endpoint(
    assignment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            "ADMIN",
            "RECEPTION",
            "TECHNICIAN",
            "OWNER"
        )
    )
):
    try:
        return get_job_assignment(
            db=db,
            assignment_id=assignment_id
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error)
        )


@router.patch(
    "/{assignment_id}/status",
    response_model=JobAssignmentResponse
)
def update_job_assignment_status_endpoint(
    assignment_id: int,
    status_data: JobAssignmentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles("ADMIN")
    )
):
    try:
        return update_job_assignment_status(
            db=db,
            assignment_id=assignment_id,
            new_status=status_data.status
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error)
        )
