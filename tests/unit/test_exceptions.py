from fastapi import status

from app.core.exceptions import (
    AppException,
    NotFoundError,
    AlreadyExistsError,
    UnauthorizedError,
    ForbiddenError,
    InvalidCredentialsError,
    TokenExpiredError,
    TokenRevokedError,
    RateLimitExceeded,
    ValidationError,
    ConflictError,
)


class TestAppException:
    """Tests for base AppException."""

    def test_app_exception_creation(self):
        """Should create exception with correct status code."""
        exc = AppException(status_code=400, detail="Test error")
        assert exc.status_code == 400
        assert exc.detail == "Test error"

    def test_app_exception_with_headers(self):
        """Should include headers when provided."""
        exc = AppException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
        assert exc.headers == {"WWW-Authenticate": "Bearer"}


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_not_found_default(self):
        """Should have default resource name."""
        exc = NotFoundError()
        assert exc.status_code == status.HTTP_404_NOT_FOUND
        assert exc.detail == "Resource not found"

    def test_not_found_custom_resource(self):
        """Should include custom resource name."""
        exc = NotFoundError("Book")
        assert exc.detail == "Book not found"


class TestAlreadyExistsError:
    """Tests for AlreadyExistsError."""

    def test_already_exists_default(self):
        """Should have default message."""
        exc = AlreadyExistsError()
        assert exc.status_code == status.HTTP_400_BAD_REQUEST
        assert exc.detail == "Resource already exists"

    def test_already_exists_custom(self):
        """Should include custom resource."""
        exc = AlreadyExistsError("User with this email")
        assert exc.detail == "User with this email already exists"


class TestUnauthorizedError:
    """Tests for UnauthorizedError."""

    def test_unauthorized_default(self):
        """Should have default message."""
        exc = UnauthorizedError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "Could not validate credentials"
        assert exc.headers == {"WWW-Authenticate": "Bearer"}

    def test_unauthorized_custom(self):
        """Should accept custom message."""
        exc = UnauthorizedError("Invalid token")
        assert exc.detail == "Invalid token"


class TestForbiddenError:
    """Tests for ForbiddenError."""

    def test_forbidden_default(self):
        """Should have default message."""
        exc = ForbiddenError()
        assert exc.status_code == status.HTTP_403_FORBIDDEN
        assert exc.detail == "Access forbidden"


class TestInvalidCredentialsError:
    """Tests for InvalidCredentialsError."""

    def test_invalid_credentials(self):
        """Should have correct status and message."""
        exc = InvalidCredentialsError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "Invalid email or password"


class TestTokenExpiredError:
    """Tests for TokenExpiredError."""

    def test_token_expired(self):
        """Should have correct status and message."""
        exc = TokenExpiredError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "Token has expired"


class TestTokenRevokedError:
    """Tests for TokenRevokedError."""

    def test_token_revoked(self):
        """Should have correct status and message."""
        exc = TokenRevokedError()
        assert exc.status_code == status.HTTP_401_UNAUTHORIZED
        assert exc.detail == "Token has been revoked"


class TestRateLimitExceeded:
    """Tests for RateLimitExceeded."""

    def test_rate_limit_default(self):
        """Should have default retry after."""
        exc = RateLimitExceeded()
        assert exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert exc.detail == "Rate limit exceeded"
        assert exc.headers == {"Retry-After": "60"}

    def test_rate_limit_custom_retry(self):
        """Should accept custom retry after."""
        exc = RateLimitExceeded(retry_after=120)
        assert exc.headers == {"Retry-After": "120"}


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self):
        """Should have correct status."""
        exc = ValidationError("Invalid input")
        assert exc.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert exc.detail == "Invalid input"


class TestConflictError:
    """Tests for ConflictError."""

    def test_conflict_error(self):
        """Should have correct status."""
        exc = ConflictError("Resource conflict")
        assert exc.status_code == status.HTTP_409_CONFLICT
        assert exc.detail == "Resource conflict"
