import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


async def get_auth_token(
    client: AsyncClient, api_prefix: str, email: str = "books@example.com"
) -> str:
    """Helper to get auth token."""
    await client.post(
        f"{api_prefix}/auth/register",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    response = await client.post(
        f"{api_prefix}/auth/login",
        json={
            "email": email,
            "password": "TestPassword123!",
        },
    )
    return response.json()["access_token"]


class TestBooksWithAuth:
    """Tests for books endpoints with authentication."""

    async def test_list_empty_books(self, client: AsyncClient, api_prefix: str):
        """Should list empty books."""
        token = await get_auth_token(client, api_prefix, "list@example.com")
        response = await client.get(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    async def test_add_book_flow(self, client: AsyncClient, api_prefix: str):
        """Full flow: add book to catalog, then to user's list."""
        token = await get_auth_token(client, api_prefix, "flow@example.com")

        catalog_response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "The Great Gatsby",
                "author": "F. Scott Fitzgerald",
                "pages_total": 180,
            },
        )
        assert catalog_response.status_code == 201
        book_id = catalog_response.json()["id"]

        user_book_response = await client.post(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "catalog_book_id": book_id,
                "status": "want_to_read",
            },
        )
        assert user_book_response.status_code == 201

        list_response = await client.get(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        data = list_response.json()
        assert len(data["items"]) == 1

    async def test_update_book(self, client: AsyncClient, api_prefix: str):
        """Should update book."""
        token = await get_auth_token(client, api_prefix, "update@example.com")

        catalog_response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Update Test",
                "author": "Author",
                "pages_total": 100,
            },
        )
        book_id = catalog_response.json()["id"]

        user_book_response = await client.post(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
            json={"catalog_book_id": book_id},
        )
        user_book_id = user_book_response.json()["id"]

        update_response = await client.patch(
            f"{api_prefix}/books/{user_book_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "reading", "pages_read": 50},
        )
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["status"] == "reading"

    async def test_delete_book(self, client: AsyncClient, api_prefix: str):
        """Should delete book."""
        token = await get_auth_token(client, api_prefix, "delete@example.com")

        catalog_response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Delete Test",
                "author": "Author",
                "pages_total": 100,
            },
        )
        book_id = catalog_response.json()["id"]

        user_book_response = await client.post(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
            json={"catalog_book_id": book_id},
        )
        user_book_id = user_book_response.json()["id"]

        delete_response = await client.delete(
            f"{api_prefix}/books/{user_book_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete_response.status_code == 204


class TestSessionsEndpoints:
    """Tests for sessions endpoints."""

    async def test_list_sessions_unauthenticated(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should require auth."""
        response = await client.get(f"{api_prefix}/books/123/sessions")
        assert response.status_code == 401

    async def test_create_session_flow(self, client: AsyncClient, api_prefix: str):
        """Full flow: create book, then create session."""
        token = await get_auth_token(client, api_prefix, "session@example.com")

        catalog_response = await client.post(
            f"{api_prefix}/catalog",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "title": "Session Test",
                "author": "Author",
                "pages_total": 100,
            },
        )
        book_id = catalog_response.json()["id"]

        user_book_response = await client.post(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
            json={"catalog_book_id": book_id},
        )
        user_book_id = user_book_response.json()["id"]

        session_response = await client.post(
            f"{api_prefix}/books/{user_book_id}/sessions",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "pages_read": 25,
                "notes": "Read chapter 1",
            },
        )
        assert session_response.status_code == 201
        data = session_response.json()
        assert data["pages_read"] == 25

        list_response = await client.get(
            f"{api_prefix}/books/{user_book_id}/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert list_response.status_code == 200
        sessions = list_response.json()
        assert len(sessions["items"]) == 1
