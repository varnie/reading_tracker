import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCatalogEndpoints:
    """Tests for catalog API endpoints."""

    async def test_get_catalog(self, client: AsyncClient, api_prefix: str):
        """Should get catalog list."""
        response = await client.get(f"{api_prefix}/catalog")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data

    async def test_get_popular_books(self, client: AsyncClient, api_prefix: str):
        """Should get popular books."""
        response = await client.get(f"{api_prefix}/catalog/popular")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_add_book_to_catalog(self, client: AsyncClient, api_prefix: str):
        """Should add book to catalog."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "catalog@example.com",
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 201

        login_response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": "catalog@example.com",
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Test Book",
                "author": "Test Author",
                "pages_total": 200,
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Test Book"

    async def test_search_catalog(self, client: AsyncClient, api_prefix: str):
        """Should search catalog."""
        response = await client.get(f"{api_prefix}/catalog?query=test")
        assert response.status_code == 200

    async def test_get_catalog_book(self, client: AsyncClient, api_prefix: str):
        """Should get a single catalog book."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": f"getbook-{uuid.uuid4()}@example.com",
                "password": "TestPassword123!",
            },
        )
        login_response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": response.json()["email"],
                "password": "TestPassword123!",
            },
        )
        token = login_response.json()["access_token"]

        create_response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Get Single Book Test",
                "author": "Test Author",
                "pages_total": 150,
            },
        )
        book_id = create_response.json()["id"]

        response = await client.get(f"{api_prefix}/catalog/{book_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book_id
        assert data["title"] == "Get Single Book Test"

    async def test_get_catalog_book_not_found(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should return 404 for non-existent book."""
        fake_id = str(uuid.uuid4())
        response = await client.get(f"{api_prefix}/catalog/{fake_id}")
        assert response.status_code == 404

    async def test_search_with_percent_character(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should handle search with percent character."""
        response = await client.get(f"{api_prefix}/catalog?query=100%")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_search_with_underscore_character(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should handle search with underscore character."""
        response = await client.get(f"{api_prefix}/catalog?query=jack_jones")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestBooksEndpoints:
    """Tests for books API endpoints."""

    async def test_list_books_unauthenticated(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should require auth for listing books."""
        response = await client.get(f"{api_prefix}/books")
        assert response.status_code == 401

    async def test_add_book_unauthenticated(self, client: AsyncClient, api_prefix: str):
        """Should require auth for adding book."""
        response = await client.post(f"{api_prefix}/books", json={})
        assert response.status_code == 401


class TestStatsEndpoints:
    """Tests for stats API endpoints."""

    async def test_get_stats_unauthenticated(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should require auth for stats."""
        response = await client.get(f"{api_prefix}/stats")
        assert response.status_code == 401

    async def test_get_top_users(self, client: AsyncClient, api_prefix: str):
        """Should get top users without auth."""
        response = await client.get(f"{api_prefix}/stats/top-users")
        assert response.status_code == 200
        data = response.json()
        assert "period" in data
        assert "users" in data

    async def test_get_top_users_with_params(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should get top users with params."""
        response = await client.get(f"{api_prefix}/stats/top-users?period=week&limit=5")
        assert response.status_code == 200
        data = response.json()
        assert data["period"] == "week"
