from celery import Celery

from .config import settings
from .database import SessionLocal

celery_app = Celery("interviewiq", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_always_eager = settings.celery_eager
celery_app.conf.broker_connection_retry_on_startup = True


@celery_app.task(name="finalize_interview")
def finalize_interview_task(interview_id: int) -> None:
    from .services import session

    db = SessionLocal()
    try:
        session.finalize(db, interview_id)
    finally:
        db.close()
