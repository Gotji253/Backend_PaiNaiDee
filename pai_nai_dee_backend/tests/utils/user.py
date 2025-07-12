from sqlalchemy.orm import Session

from ...app.crud import crud_user
from ...app.models.user import User
from ...app.schemas.user import UserCreate
from .utils import random_lower_string


def create_random_user(db: Session) -> User:
    username = random_lower_string()
    password = random_lower_string()
    user_in = UserCreate(username=username, password=password)
    user = crud_user.create(db=db, obj_in=user_in)
    return user
