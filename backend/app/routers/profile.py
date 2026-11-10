from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..deps import get_current_user
from ..services import memory

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=schemas.ProfileOut)
def profile(user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return memory.build_profile(db, user.id)
