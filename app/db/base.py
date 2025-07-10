from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import Column, Integer, MetaData
from sqlalchemy.ext.declarative import as_declarative, declared_attr

# Recommended naming convention for metadata
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=convention)

@as_declarative(metadata=metadata)
class Base:
    """Base class which provides automated table name
    and surrogate primary key column.
    """

    @declared_attr
    def __tablename__(cls) -> str:
        # Makes table names like 'users', 'places' from class names User, Place
        # Handles potential pluralization issues better manually if needed,
        # but for simple cases, lowercasing and adding 's' is common.
        # If a __tablename__ is set in the model, that will be used instead.
        if hasattr(cls, "__tablename__"):
            return cls.__tablename__
        return cls.__name__.lower() + "s"


    id: Column = Column(Integer, primary_key=True, index=True)


# Function to create all tables
def create_db_and_tables(engine):
    # This import is crucial here to ensure all models are loaded
    # and registered with Base.metadata before create_all is called.
    # Import all the models, so that Base has them before being
    # imported by Alembic or used directly by create_all
    # from app.models import User, Place, Trip, Review # noqa
    # The above line is not strictly necessary if models are imported elsewhere before this runs,
    # but it's a safeguard. A better place is in main.py or a db setup script.
    Base.metadata.create_all(bind=engine)
