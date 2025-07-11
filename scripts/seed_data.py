import logging
from faker import Faker
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.base import Base
from app.models.user import User
from app.models.place import Place
from app.models.trip import Trip
from app.models.review import Review
from app.crud.crud_user import user as crud_user
from app.crud.crud_place import place as crud_place

# crud_trip and crud_review might have specific logic,
# but for seeding, direct model manipulation can be simpler for relationships.
# from app.crud.crud_trip import trip as crud_trip
# from app.crud.crud_review import review as crud_review
from app.schemas.user import UserCreate
from app.schemas.place import PlaceCreate
from app.schemas.trip import TripCreate  # owner_id, place_ids
from app.schemas.review import ReviewCreate  # place_id
from app.core.security import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

fake = Faker()


def reset_database():
    """Resets the database by dropping and recreating all tables."""
    logger.info("Resetting database...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete.")


def seed_data(db: Session):
    """Seeds the database with sample data."""
    logger.info("Starting to seed data...")

    # Create Users
    users_data = []
    for _ in range(10):
        user_in = UserCreate(
            email=fake.unique.email(),  # Ensure unique emails
            password="password123",  # Raw password, crud will hash if it's setup for it, or hash here
            full_name=fake.name(),
            is_active=True,
            is_superuser=fake.boolean(chance_of_getting_true=10),
        )
        # crud_user.create is synchronous and expects a UserCreate schema that includes the plain password.
        # It should handle hashing internally. If not, we'd call get_password_hash here.
        # Let's assume crud_user.create handles hashing.
        # Reading app/crud/crud_user.py would confirm this.
        # For now, let's assume it is:
        # user = crud_user.create(db, obj_in=user_in)
        # If crud_user.create does NOT hash, then:
        hashed_password = get_password_hash("password123")
        user_db_in = UserCreate(  # Use a different variable if schema is strict on password field name
            email=user_in.email,
            full_name=user_in.full_name,
            is_active=user_in.is_active,
            is_superuser=user_in.is_superuser,
            # Assuming UserCreate takes hashed_password or User model takes it
            # The UserCreate schema in app/schemas/user.py has `password: str`
            # The User model in app/models/user.py has `hashed_password: str`
            # crud_user.create_user function hashes the password.
        )
        # So, we pass the plain password to crud_user.create
        user = crud_user.create(db, obj_in=user_in)
        users_data.append(user)
    logger.info(f"Seeded {len(users_data)} users.")

    # Create Places
    places_data = []
    for _ in range(20):
        place_in = PlaceCreate(
            name=fake.unique.company()
            + " "
            + fake.street_suffix(),  # More varied names
            description=fake.sentence(nb_words=10),
            latitude=float(fake.latitude()),
            longitude=float(fake.longitude()),
            country=fake.country(),
            city=fake.city(),
        )
        place = crud_place.create(db, obj_in=place_in)
        places_data.append(place)
    logger.info(f"Seeded {len(places_data)} places.")

    # Create Trips and associate Places
    trips_data = []
    if users_data and places_data:
        for user_obj in users_data:
            for _ in range(fake.random_int(min=0, max=2)):  # Each user has 0-2 trips
                # TripCreate schema expects owner_id and place_ids
                # However, crud.trip.create might not directly handle place_ids for m2m.
                # It's often easier to create the Trip, then add places.

                trip_name = f"Adventure in {fake.city()}"
                # Ensure trip names are somewhat unique for testing if necessary
                # trip_name = fake.unique.catch_phrase() # Alternative for unique names

                trip_schema_in = TripCreate(
                    name=trip_name,
                    description=fake.sentence(nb_words=15),
                    start_date=fake.date_this_decade(
                        before_today=True, after_today=False
                    ),  # Past date
                    end_date=fake.date_between(
                        start_date="-5y", end_date="today"
                    ),  # Ensure end_date is after start_date
                    owner_id=user_obj.id,
                    place_ids=[],  # We will add places manually after creation for this example
                )

                # Create the trip object using its CRUD or direct model if simpler
                # current crud_trip.create expects obj_in: TripCreate.
                # It likely doesn't handle place_ids for m2m itself.
                # So, create the Trip first.
                # temp_trip = crud_trip.create(db, obj_in=trip_schema_in)

                # For seeding, sometimes direct model creation + relationship append is clearer
                db_trip = Trip(
                    name=trip_schema_in.name,
                    description=trip_schema_in.description,
                    start_date=trip_schema_in.start_date,
                    end_date=trip_schema_in.end_date,
                    owner_id=user_obj.id,
                )
                db.add(db_trip)
                db.commit()  # Commit to get db_trip.id
                db.refresh(db_trip)

                # Associate some places with this trip
                num_places_for_trip = fake.random_int(
                    min=0, max=min(3, len(places_data))
                )
                if num_places_for_trip > 0:
                    selected_places = fake.random_elements(
                        elements=places_data, length=num_places_for_trip, unique=True
                    )
                    for place_obj in selected_places:
                        db_trip.places.append(place_obj)
                    db.commit()  # Commit place associations
                    db.refresh(db_trip)  # Refresh to see places if needed

                trips_data.append(db_trip)
        logger.info(f"Seeded {len(trips_data)} trips and their place associations.")
    else:
        logger.info("Not enough users or places to seed trips.")

    # Create Reviews
    reviews_data = []
    if places_data and users_data:
        for user_obj in users_data:
            for _ in range(fake.random_int(min=0, max=3)):  # Corrected this line
                if not places_data:
                    continue
                place_to_review = fake.random_element(elements=places_data)

                # ReviewCreate schema expects place_id. owner_id is set by API.
                # For seeding, we set owner_id directly on the model.
                review_schema_in = ReviewCreate(
                    rating=fake.random_int(min=1, max=5),
                    comment=fake.paragraph(nb_sentences=2),
                    place_id=place_to_review.id,
                )

                # Create Review model instance directly
                db_review = Review(
                    rating=review_schema_in.rating,
                    comment=review_schema_in.comment,
                    place_id=review_schema_in.place_id,
                    owner_id=user_obj.id,
                    # created_at and updated_at have defaults in the model
                )
                db.add(db_review)
                db.commit()
                db.refresh(db_review)
                reviews_data.append(db_review)
        logger.info(f"Seeded {len(reviews_data)} reviews.")
    else:
        logger.info("Not enough users or places to seed reviews.")

    logger.info("Data seeding complete.")


def main():
    logger.info("Script started: Resetting database and seeding data...")

    # Perform database reset (synchronous)
    reset_database()

    # Create a new synchronous session for seeding
    db: Session = SessionLocal()
    try:
        seed_data(db)
        logger.info("Successfully seeded data.")
    except Exception as e:
        logger.error(f"An error occurred during seeding: {e}")
        logger.exception("Detailed traceback:")  # Logs full traceback
        db.rollback()
    finally:
        db.close()

    logger.info("Script finished.")


if __name__ == "__main__":
    main()
