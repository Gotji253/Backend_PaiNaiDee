# This file makes the 'models' directory a Python package.
# It can also be used to conveniently import model classes.

from .user import User
from .place import Place
from .review import Review
from .favorite import user_favorites # This is the association table, not a model class in the same way

# You might also want to import Base from database.py here if models need it directly,
# but typically models inherit from Base defined in database.py, which imports them.

# The line `from .models import user, place, review, favorite` in database.py
# will work if this __init__.py correctly exposes these names or if
# database.py imports them directly as `from .models.user import User`, etc.

# For the import `from .models import user, place, review, favorite` in database.py to work
# as intended (i.e., `user` refers to the module `user.py`), this __init__.py doesn't
# strictly need to do anything more than exist. However, to make individual model classes
# accessible directly via `from app.models import User`, then the imports above are useful.
# The current import in database.py (`from .models import user, place, review, favorite`)
# actually imports the modules themselves. So, in database.py, it would be `user.User`, etc.
# To allow `models.User` after `from . import models`, this __init__.py is fine.

# Let's ensure that the models are available when `Base.metadata.create_all` is called.
# The imports in `database.py` like `from .models.user import User` (if we changed to that)
# or the current `from .models import user` (module) and then accessing `user.User`
# are patterns to ensure SQLAlchemy's Base knows about all model definitions.
# The current setup in database.py (importing the modules) is fine.
# This __init__.py is mostly for package structure and potentially easier imports elsewhere.
# No changes strictly needed here for database.py to function as modified,
# as long as the file structure is `app/models/user.py`, `app/models/place.py`, etc.

# The current imports in database.py:
# from .models import user, place, review, favorite
# This means database.py can then use:
# user.User
# place.Place
# review.Review
# favorite.user_favorites (this is the table object itself)
# This is a valid way to ensure Base.metadata knows about the tables.
# So this __init__.py is primarily for marking the directory as a package.
# The example imports (User, Place, Review) are good for other parts of the app that might do:
# from app.models import User, Place, Review
# No change needed to this file based on the database.py update. It's fine as is.
# For clarity and to support `from app.models import User` etc., let's ensure the classes are exported:
# This is already done by the existing template for __init__.py files.

# To be explicit for `Base.metadata.create_all(bind=engine)` to find the tables,
# the modules containing table definitions must be imported before `create_all` is called.
# `database.py` now does `from .models import user, place, review, favorite`.
# This means `user.User.__table__`, `place.Place.__table__`, `review.Review.__table__`,
# and `favorite.user_favorites` (which is already a Table object) will be known to `Base.metadata`.
# This is correct.

# The current content of this __init__.py is:
# (empty or just a comment)
# Let's make it export the models for easier access from other modules if they do `from app.models import User`

# from .user import User
# from .place import Place
# from .review import Review
# from .favorite import user_favorites # This is an object, not a class in the same way

# Actually, the `ls` output shows this file was already created (likely by me).
# Let's ensure it properly exports the models so that `from ..models import user` in `database.py`
# makes `user.User` available.
# If `database.py` has `from .models.user import User`, then this `__init__.py` is less critical for that specific import.
# But if `database.py` has `from .models import user`, then `user` is the module `user.py`.

# The current `database.py` has `from .models import user, place, review, favorite`.
# This means in `database.py`, we are referring to `user.User`, `place.Place`, etc.
# This is fine. The `__init__.py` can remain simple or export the classes for convenience elsewhere.
# For maximum clarity and to support `from app.models import User` elsewhere:
from .user import User
from .place import Place
from .review import Review
from .favorite import user_favorites # Association table, not a model class like others

# This ensures that when `database.py` does `from .models import user, place, review, favorite`,
# it correctly loads these modules, and thus their defined SQLAlchemy models become known to `Base`.
# The content I'm providing here makes User, Place, Review classes and user_favorites table
# available if someone imports `from app.models import ...`.
# The way database.py imports `user`, `place`, etc., as modules is also correct.
# So, this __init__.py is more for general convenience.
# The crucial part is that the modules defining models are imported before Base.metadata.create_all.
# The change in database.py ensures this.
# This file should list the main classes/objects for easier import if desired.
# The current content of this file if it was just `touch` would be empty.
# So let's fill it.
