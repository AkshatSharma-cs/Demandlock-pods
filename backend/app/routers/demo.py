from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db import get_db
from ..models import Student, User

router = APIRouter()


@router.get("/demo/users")
def demo_users(db: Session = Depends(get_db)) -> list[dict]:
    if not settings.demo_mode:
        raise HTTPException(404, "Demo mode is disabled")
    students = {student.user_id: student.id for student in db.scalars(select(Student)).all()}
    return [
        {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "language": user.language,
            "age_band": user.age_band,
            "student_id": students.get(user.id),
        }
        for user in db.scalars(select(User).order_by(User.name)).all()
    ]
