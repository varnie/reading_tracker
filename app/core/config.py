from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_env: str = Field(default="development", validation_alias="APP_ENV")
    app_host: str = Field(default="0.0.0.0", validation_alias="APP_HOST")
    app_port: int = Field(default=8000, validation_alias="APP_PORT")
    app_name: str = "Reading Tracker API"
    app_version: str = "v1"
    debug: bool = False

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/reading_tracker",
        validation_alias="DATABASE_URL",
    )
    database_pool_size: int = Field(default=5, validation_alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(
        default=10, validation_alias="DATABASE_MAX_OVERFLOW"
    )

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        validation_alias="REDIS_URL",
    )

    # JWT
    jwt_secret_key: str = Field(
        default="change-me-in-production-use-openssl-rand-hex-32",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", validation_alias="JWT_ALGORITHM")
    access_token_lifetime_minutes: int = Field(
        default=30, validation_alias="ACCESS_TOKEN_LIFETIME_MINUTES"
    )
    refresh_token_lifetime_days: int = Field(
        default=7, validation_alias="REFRESH_TOKEN_LIFETIME_DAYS"
    )

    # Argon2
    argon2_memory_cost: int = Field(
        default=65536, validation_alias="ARGON2_MEMORY_COST"
    )
    argon2_time_cost: int = Field(default=3, validation_alias="ARGON2_TIME_COST")
    argon2_parallelism: int = Field(default=4, validation_alias="ARGON2_PARALLELISM")

    # Rate Limiting
    rate_limit_per_minute: int = Field(
        default=60, validation_alias="RATE_LIMIT_PER_MINUTE"
    )
    rate_limit_auth_per_minute: int = Field(
        default=10, validation_alias="RATE_LIMIT_AUTH_PER_MINUTE"
    )

    # CORS
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:8080",
        validation_alias="CORS_ORIGINS",
    )

    # Email
    smtp_host: str = Field(default="localhost", validation_alias="SMTP_HOST")
    smtp_port: int = Field(default=587, validation_alias="SMTP_PORT")
    smtp_user: str = Field(default="", validation_alias="SMTP_USER")
    smtp_password: str = Field(default="", validation_alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(
        default="noreply@readingtracker.app", validation_alias="SMTP_FROM_EMAIL"
    )
    smtp_from_name: str = Field(
        default="Reading Tracker", validation_alias="SMTP_FROM_NAME"
    )
    smtp_tls: bool = Field(default=True, validation_alias="SMTP_TLS")
    email_enabled: bool = Field(default=False, validation_alias="EMAIL_ENABLED")

    # Celery
    celery_broker_url: str = Field(
        default="redis://localhost:6379/1",
        validation_alias="CELERY_BROKER_URL",
    )
    celery_result_backend: str = Field(
        default="redis://localhost:6379/2",
        validation_alias="CELERY_RESULT_BACKEND",
    )

    # Logging
    log_level: str = Field(default="INFO", validation_alias="LOG_LEVEL")

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


settings = Settings()
