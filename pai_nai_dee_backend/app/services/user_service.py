from sqlalchemy.orm import Session
from fastapi import Depends # Import Depends

# from app import crud, schemas, models
# from app.core.security import get_password_hash # Example import


class UserService:
    def __init__(self, db: Session):
        self.db = db

    # Example of a more complex operation that might be in a service:
    # def register_new_user_with_welcome_email(self, user_in: schemas.UserCreate) -> models.User:
    #     # Check for existing user (could also be in CRUD or router, depends on flow)
    #     existing_user = crud.crud_user.get_user_by_username(self.db, username=user_in.username)
    #     if existing_user:
    #         # raise appropriate exception
    #         pass
    #
    #     user = crud.crud_user.create_user(self.db, user_in=user_in)
    #
    #     # Send welcome email (pseudo-code)
    #     # email_service.send_welcome_email(to=user.email, username=user.username)
    #
    #     return user

    # Placeholder for future user-related business logic
    def get_user_profile_details(self, user_id: int):
        """
        Example: Fetches user and formats a more complex profile,
        potentially aggregating data from other services or models.
        """
        # user = crud.crud_user.get_user(self.db, user_id)
        # if not user:
        #     return None
        # # ... more logic ...
        # return {"username": user.username, "email": user.email, "total_reviews": len(user.reviews)}
        pass


def get_user_service(db: Session = Depends(lambda: None)) -> UserService:  # type: ignore
    """
    Dependency injector for UserService.
    Allows db session to be injected if this service is used as a FastAPI dependency.
    For now, it's instantiated directly where needed.
    """
    # This is a bit tricky. If services are used as FastAPI Depends, they need this.
    # If they are instantiated directly by routers, the router provides the db session.
    # Let's assume for now they might be instantiated by routers/other services.
    # To make it usable as a FastAPI dependency:
    # from app.db.database import (
    #     get_db,
    # )  # Local import to avoid circular if service used globally. F401: Unused.
    # from fastapi import Depends as FastAPI今のDepends  # Alias to avoid conflict. F401: Unused.

    # This pattern is more if the service itself is a FastAPI dependency.
    # def get_user_service_dependency(db: Session = FastAPI今のDepends(get_db)):
    #    return UserService(db)
    # return get_user_service_dependency

    # If services are meant to be instantiated manually in routers:
    # router: db_session = Depends(get_db)
    # user_service = UserService(db_session)
    # For now, let's not make it a FastAPI dependency itself.
    # Routers will get db session and pass it to service constructor.
    pass


# Example of how a router might use it:
# from app.services.user_service import UserService
# from app.db.database import get_db
#
# @router.post("/users/register_special")
# def register_user_special(user_in: schemas.UserCreate, db: Session = Depends(get_db)):
#     user_service = UserService(db)
#     return user_service.register_new_user_with_welcome_email(user_in)
