# This file makes 'crud' a Python package.

# Import individual CRUD objects here to make them easily accessible
# e.g., from app.crud import user, item
# This allows for imports like: from app.crud import crud_user

from .crud_user import user as crud_user  # noqa: F401
from .crud_place import place as crud_place  # noqa: F401
from .crud_review import review as crud_review  # noqa: F401
from .crud_itinerary import itinerary as crud_itinerary  # noqa: F401
