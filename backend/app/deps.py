from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session  

from . import models
from .database import get_db
from .security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def user_from_token(db: Session, token: str) -> models.User | None:
    user_id = decode_token(token)
    return db.get(models.User, user_id) if user_id else None


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> models.User:
    user = user_from_token(db, token)
    if not user:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired token")
    return user


def get_owned_interview(interview_id: int, user: models.User, db: Session) -> models.Interview:
    interview = db.get(models.Interview, interview_id)
    if not interview or interview.user_id != user.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Interview not found")
    return interview
