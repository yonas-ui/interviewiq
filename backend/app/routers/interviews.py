from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user, get_owned_interview
from ..services import memory, session
from ..worker import finalize_interview_task

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


def _start(db: Session, interview: models.Interview) -> models.Interview:
    db.add(interview)
    db.commit()
    session.ask_next(db, interview)
    db.refresh(interview)
    return interview


@router.post("", response_model=schemas.InterviewOut, status_code=201)
def create_interview(
    data: schemas.InterviewCreate,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return _start(db, models.Interview(user_id=user.id, **data.model_dump()))


@router.post("/practice", response_model=schemas.InterviewOut, status_code=201)
def create_practice(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Personal improvement system: a session built from the candidate's weakest skills."""
    weak = memory.get_memory(db, user.id)["weak"]
    if not weak:
        raise HTTPException(400, "Complete an interview first so we can find your weak spots")
    last = (
        db.query(models.Interview)
        .filter(models.Interview.user_id == user.id)
        .order_by(models.Interview.id.desc())
        .first()
    )
    interview = models.Interview(
        user_id=user.id,
        role=last.role if last else "Software Engineer",
        level=last.level if last else "mid",
        interview_type="technical",
        focus="Practice weak skills: " + ", ".join(weak),
    )
    return _start(db, interview)


@router.get("", response_model=list[schemas.InterviewSummary])
def list_interviews(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(models.Interview)
        .filter(models.Interview.user_id == user.id)
        .order_by(models.Interview.id.desc())
        .all()
    )


@router.get("/{interview_id}", response_model=schemas.InterviewOut)
def get_interview(interview_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return get_owned_interview(interview_id, user, db)


@router.post("/{interview_id}/answer", response_model=schemas.AnswerOut)
def answer(
    interview_id: int,
    data: schemas.AnswerIn,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """REST fallback for the WebSocket flow."""
    interview = get_owned_interview(interview_id, user, db)
    try:
        turn, nxt = session.submit_answer(db, interview, data.text, data.code)
    except ValueError as exc:
        raise HTTPException(400, str(exc))
    return schemas.AnswerOut(evaluation=turn.evaluation, next=nxt)


@router.post("/{interview_id}/finish", response_model=schemas.InterviewOut)
def finish(interview_id: int, user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    interview = get_owned_interview(interview_id, user, db)
    if interview.status == "active":
        interview.status = "evaluating"
        db.commit()
        try:
            finalize_interview_task.delay(interview.id)
        except Exception:  # broker down: evaluate inline instead of losing the report
            session.finalize(db, interview.id)
        db.refresh(interview)
    return interview
