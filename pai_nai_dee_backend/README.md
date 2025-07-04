# Pai Nai Dee API Backend

This is the backend API for the Pai Nai Dee travel planning application, built with FastAPI.

## Project Overview

The Pai Nai Dee API provides endpoints for managing users, places, reviews, and travel itineraries. It features a modular structure designed for scalability and maintainability, utilizing FastAPI, SQLAlchemy for ORM, Alembic for database migrations, and Pydantic for data validation. Authentication is handled via JWT.

### Key Technologies
- **FastAPI**: For building the high-performance API.
- **SQLAlchemy**: For database interaction (ORM).
- **Pydantic**: For data validation and settings management.
- **Alembic**: For database migrations.
- **JWT**: For user authentication.
- **Pytest**: For running automated tests.
- **Uvicorn**: As the ASGI server.
- **Python 3.11+**

### Core Features
- User registration and JWT-based authentication.
- CRUD operations for Users, Places, Reviews, and Itineraries.
- Modular structure separating concerns into:
    - `core`: Configuration, security, logging.
    - `db`: Database session management and Alembic setup.
    - `models`: SQLAlchemy ORM models.
    - `schemas`: Pydantic data validation schemas.
    - `crud`: Reusable CRUD operations for database interactions.
    - `api`: FastAPI routers and API endpoint definitions.
    - `services`: Business logic layer.
    - `tests`: Unit and integration tests.
- Environment-based configuration using `.env` files.
- Basic logging and custom error handling.
- Prepared for future feature expansion (e.g., recommendation system, advanced search, social features).

## Project Structure

```
pai_nai_dee_backend/
├── alembic/                  # Alembic migration scripts
├── alembic.ini               # Alembic configuration
├── app/                      # Main application module
│   ├── __init__.py
│   ├── api/                  # API routers and versioning
│   │   ├── __init__.py
│   │   ├── api_v1/
│   │   │   ├── __init__.py
│   │   │   └── api.py        # Main v1 API router
│   │   └── endpoints/        # Individual resource endpoints (users, places, etc.)
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── ...
│   ├── core/                 # Core components (config, security, logging)
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── logging.py
│   │   └── security.py
│   ├── crud/                 # CRUD operations for database interaction
│   │   ├── __init__.py
│   │   └── crud_user.py
│   │   └── ...
│   ├── db/                   # Database setup and session management
│   │   ├── __init__.py
│   │   └── database.py
│   ├── main.py               # FastAPI application entry point
│   ├── models/               # SQLAlchemy ORM models
│   │   ├── __init__.py
│   │   └── user.py
│   │   └── ...
│   ├── schemas/              # Pydantic schemas for data validation
│   │   ├── __init__.py
│   │   └── user.py
│   │   └── ...
│   ├── services/             # Business logic layer
│   │   ├── __init__.py
│   │   └── user_service.py
│   │   └── ...
│   └── utils.py              # General utility functions (if any)
├── tests/                    # Automated tests
│   ├── __init__.py
│   ├── conftest.py           # Pytest configuration and fixtures
│   ├── api/                  # API endpoint tests
│   │   └── __init__.py
│   │   └── test_users.py
│   └── test_main.py
├── .env.example              # Example environment variables file
├── .gitignore
├── Dockerfile                # Example Dockerfile (if containerization is used)
├── README.md
└── requirements.txt
```

## Getting Started

### Prerequisites
- Python 3.11 or higher
- Pip (Python package installer)
- A PostgreSQL database (or modify `DATABASE_URL` in `.env` for SQLite, etc.)
- Git

### Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd pai_nai_dee_backend
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    -   Copy the example `.env.example` file to `.env`:
        ```bash
        cp .env.example .env
        ```
    -   Modify the `.env` file with your actual database credentials, secret key, etc.
        Key variables to check:
        - `DATABASE_URL` (or individual `POSTGRES_*` variables)
        - `SECRET_KEY` (generate a strong random key)

5.  **Database Migrations:**
    -   Ensure your database server is running and accessible with the credentials in your `.env` file.
    -   Apply database migrations using Alembic:
        ```bash
        alembic upgrade head
        ```
    -   If you make changes to SQLAlchemy models in `app/models/`, you'll need to generate a new migration:
        ```bash
        alembic revision -m "Describe your model changes here" --autogenerate
        alembic upgrade head
        ```

### Running the Application

-   **Using Uvicorn (for development):**
    From the `pai_nai_dee_backend` directory:
    ```bash
    uvicorn app.main:app --reload
    ```
    The API will typically be available at `http://127.0.0.1:8000`.
    The API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.
    Alternative documentation (ReDoc) at `http://127.0.0.1:8000/redoc`.

### Running Tests

-   Tests are located in the `tests/` directory and use `pytest`.
-   The test suite includes API tests and database-specific tests (for stored procedures, triggers, and migrations).
-   To run all tests, from the `pai_nai_dee_backend` directory:
    ```bash
    pytest
    ```
-   By default, API tests might still use a SQLite database as per original setup if `TEST_DATABASE_URL` is not overridden by PostgreSQL settings for all tests. The new database tests specifically target PostgreSQL.

### Setting up for Database Tests (PostgreSQL)

The database tests (`tests/db/`) require a running PostgreSQL instance and specific environment variables to be set. These tests will create a template database and then clone it for each test function, ensuring test isolation.

1.  **Ensure PostgreSQL is running and accessible.** You can use Docker:
    ```bash
    docker run --name painaidee-test-postgres -e POSTGRES_USER=test_user -e POSTGRES_PASSWORD=test_password -p 5433:5432 -d postgres:13
    ```
    Adjust `POSTGRES_USER` and `POSTGRES_PASSWORD` if you use different values in your `.env` file for testing. The port `5433` is used here to avoid conflict with a potential default development PostgreSQL on `5432`.

2.  **Set Environment Variables for Testing:**
    These variables are defined in `app/core/config.py` and should be set in your environment or in the `.env` file (which is loaded by Pydantic settings).
    -   `TEST_POSTGRES_USER`: Username for the PostgreSQL test server (e.g., `test_user`). This user needs `CREATEDB` privileges.
    -   `TEST_POSTGRES_PASSWORD`: Password for the test user.
    -   `TEST_POSTGRES_SERVER`: Hostname or IP of the test PostgreSQL server (e.g., `localhost`).
    -   `TEST_POSTGRES_PORT`: Port of the test PostgreSQL server (e.g., `5433`).
    -   `TEST_POSTGRES_DB_MAIN`: Name for the template database that will be created and migrated (e.g., `painaidee_test_template`).

    Example for your `.env` file:
    ```env
    # ... other variables ...

    # For PostgreSQL Database Tests
    TEST_POSTGRES_USER=test_user
    TEST_POSTGRES_PASSWORD=test_password
    TEST_POSTGRES_SERVER=localhost
    TEST_POSTGRES_PORT=5433
    TEST_POSTGRES_DB_MAIN=painaidee_test_template
    ```
    Ensure these match the user/password you used when starting your PostgreSQL test instance if you are managing it manually or via Docker. The `test_user` must have permissions to create new databases on the PostgreSQL server.

3.  **Running Specific Test Types:**
    -   To run only database tests:
        ```bash
        pytest tests/db
        ```
    -   To run only API tests:
        ```bash
        pytest tests/api
        ```

-   The database test setup (`tests/conftest.py`) handles the creation of a template database (`TEST_POSTGRES_DB_MAIN`) with all migrations applied. Then, for each test function in `tests/db/`, a new database is cloned from this template and dropped after the test, providing a clean environment.

## API Endpoints

The API is versioned, with the current version being v1, accessible under the `/api/v1` prefix.

Key endpoint categories:
-   `/auth`: Authentication (token generation).
-   `/users`: User management.
-   `/places`: Place information and search.
-   `/reviews`: Review submission and retrieval.
-   `/itineraries`: Itinerary creation and management.

Refer to the interactive API documentation at `/docs` (Swagger UI) or `/redoc` when the application is running for detailed information on all available endpoints, request/response schemas, and how to interact with them.

## Future Development

This project is structured to support future expansion, including but not limited to:
-   **Recommendation System**: Personalized place recommendations.
-   **Advanced Search**: More complex filtering and geospatial search for places.
-   **Social Features**: User following, sharing itineraries, community feeds.
-   **Notifications**: For updates, new reviews on bookmarked places, etc.
-   **Image Uploads**: For places and user profiles.
-   **Background Tasks**: For handling long-running processes (e.g., sending emails, data processing).

## Contributing

Details on contributing to the project will be added here (e.g., coding standards, pull request process).
For now, ensure code is formatted with Black and passes Flake8 linting.
```bash
black .
flake8 .
```

---

This README provides a comprehensive guide to understanding, setting up, and running the Pai Nai Dee API backend.
```
