import pytest
from httpx import AsyncClient  # Use AsyncClient from httpx for async app
from fastapi import status  # For status codes

# Fixtures like `client` and `db` are automatically injected by pytest from conftest.py


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """
    Tests the /health endpoint.
    """
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """
    Tests the root / endpoint.
    """
    response = await client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to Pai Nai Dee API"}


@pytest.mark.asyncio
async def test_api_v1_root_endpoint(client: AsyncClient):
    """
    Tests the /api/v1/ endpoint.
    """
    from app.core.config import settings  # To get API_V1_STR

    response = await client.get(settings.API_V1_STR + "/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Welcome to Pai Nai Dee API v1"}
