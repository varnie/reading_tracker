import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestHealth:
    """Tests for health endpoint."""

    async def test_health_check(self, client: AsyncClient):
        """Health endpoint should return healthy status."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestAuthRegister:
    """Tests for registration endpoint."""

    async def test_register_success(self, client: AsyncClient, api_prefix: str):
        """Should register new user successfully."""
        email = f"test-{uuid.uuid4()}@example.com"
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == email
        assert "id" in data

    async def test_register_duplicate_email(self, client: AsyncClient, api_prefix: str):
        """Should fail if email already exists."""
        email = f"duplicate-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": email,
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 400

    async def test_register_invalid_email(self, client: AsyncClient, api_prefix: str):
        """Should fail with invalid email."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": "not-an-email",
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 422

    async def test_register_short_password(self, client: AsyncClient, api_prefix: str):
        """Should fail with short password."""
        response = await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": f"test-{uuid.uuid4()}@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422


class TestAuthLogin:
    """Tests for login endpoint."""

    async def test_login_success(self, client: AsyncClient, api_prefix: str):
        """Should login successfully."""
        email = f"login-{uuid.uuid4()}@example.com"
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
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_jti" in data
        assert data["token_type"] == "bearer"

    async def test_login_invalid_credentials(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should fail with wrong password."""
        email = f"user-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={
                "email": email,
                "password": "CorrectPassword123!",
            },
        )
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": email,
                "password": "WrongPassword123!",
            },
        )
        assert response.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient, api_prefix: str):
        """Should fail for nonexistent user."""
        response = await client.post(
            f"{api_prefix}/auth/login",
            json={
                "email": f"nonexistent-{uuid.uuid4()}@example.com",
                "password": "TestPassword123!",
            },
        )
        assert response.status_code == 401


class TestAuthLogout:
    """Tests for logout endpoint."""

    async def test_logout_success(self, client: AsyncClient, api_prefix: str):
        """Should logout successfully."""
        email = f"logout-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={"email": email, "password": "TestPassword123!"},
        )
        login_resp = await client.post(
            f"{api_prefix}/auth/login",
            json={"email": email, "password": "TestPassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = await client.post(
            f"{api_prefix}/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Logged out successfully"

        # Access token should be rejected after logout (blacklist enforced).
        protected_resp = await client.get(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert protected_resp.status_code == 401

    async def test_logout_without_token(self, client: AsyncClient, api_prefix: str):
        """Should logout even without token (no-op)."""
        response = await client.post(f"{api_prefix}/auth/logout")
        assert response.status_code == 200


class TestAuthRefresh:
    """Tests for token refresh endpoint."""

    async def test_refresh_success(self, client: AsyncClient, api_prefix: str):
        """Should refresh token successfully."""
        email = f"refresh-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={"email": email, "password": "TestPassword123!"},
        )
        login_resp = await client.post(
            f"{api_prefix}/auth/login",
            json={"email": email, "password": "TestPassword123!"},
        )
        refresh_token = login_resp.json()["refresh_token"]

        response = await client.post(
            f"{api_prefix}/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "expires_in" in data
        assert data["token_type"] == "bearer"

        new_refresh_token = data["refresh_token"]

        # Old refresh token should be revoked after rotation.
        old_refresh_resp = await client.post(
            f"{api_prefix}/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )
        assert old_refresh_resp.status_code == 401

        # New refresh token should work.
        new_refresh_resp = await client.post(
            f"{api_prefix}/auth/refresh",
            cookies={"refresh_token": new_refresh_token},
        )
        assert new_refresh_resp.status_code == 200

    async def test_refresh_without_token(self, client: AsyncClient, api_prefix: str):
        """Should fail without refresh token."""
        response = await client.post(f"{api_prefix}/auth/refresh")
        assert response.status_code == 401


class TestAuthProtectedEndpoints:
    """Tests for protected endpoints requiring authentication."""

    async def test_get_books_with_auth(self, client: AsyncClient, api_prefix: str):
        """Should access protected endpoint with valid token."""
        email = f"protected-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={"email": email, "password": "TestPassword123!"},
        )
        login_resp = await client.post(
            f"{api_prefix}/auth/login",
            json={"email": email, "password": "TestPassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            f"{api_prefix}/books",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200

    async def test_get_books_with_invalid_token(
        self, client: AsyncClient, api_prefix: str
    ):
        """Should reject invalid token."""
        response = await client.get(
            f"{api_prefix}/books",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert response.status_code == 401

    async def test_get_books_without_token(self, client: AsyncClient, api_prefix: str):
        """Should reject request without token."""
        response = await client.get(f"{api_prefix}/books")
        assert response.status_code == 401

    async def test_get_stats_with_auth(self, client: AsyncClient, api_prefix: str):
        """Should access stats with valid token."""
        email = f"stats-{uuid.uuid4()}@example.com"
        await client.post(
            f"{api_prefix}/auth/register",
            json={"email": email, "password": "TestPassword123!"},
        )
        login_resp = await client.post(
            f"{api_prefix}/auth/login",
            json={"email": email, "password": "TestPassword123!"},
        )
        token = login_resp.json()["access_token"]

        response = await client.get(
            f"{api_prefix}/stats",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_books" in data


class TestCatalog:
    """Tests for catalog endpoints."""

    async def test_search_catalog(self, client: AsyncClient, api_prefix: str):
        """Should search catalog."""
        response = await client.get(f"{api_prefix}/catalog")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data

    async def test_search_with_query(self, client: AsyncClient, api_prefix: str):
        """Should search with query parameter."""
        response = await client.get(f"{api_prefix}/catalog?query=1984")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data


class TestBooksUnauthenticated:
    """Tests for books endpoints without authentication."""

    async def test_list_books_requires_auth(self, client: AsyncClient, api_prefix: str):
        """Should require authentication."""
        response = await client.get(f"{api_prefix}/books")
        assert response.status_code == 401

    async def test_add_book_requires_auth(self, client: AsyncClient, api_prefix: str):
        """Should require authentication."""
        response = await client.post(f"{api_prefix}/books", json={})
        assert response.status_code == 401
