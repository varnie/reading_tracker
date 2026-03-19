from app.shared.events import Event


class AuthEvents:
    """Events emitted by auth feature."""

    @staticmethod
    def user_registered(user_id: str, email: str) -> Event:
        """Emitted when a new user registers."""
        return Event(
            name="auth.user_registered",
            data={
                "user_id": user_id,
                "email": email,
            },
            metadata={"source": "auth"},
        )

    @staticmethod
    def user_logged_in(user_id: str) -> Event:
        """Emitted when a user logs in."""
        return Event(
            name="auth.user_logged_in",
            data={"user_id": user_id},
            metadata={"source": "auth"},
        )

    @staticmethod
    def user_logged_out(user_id: str) -> Event:
        """Emitted when a user logs out."""
        return Event(
            name="auth.user_logged_out",
            data={"user_id": user_id},
            metadata={"source": "auth"},
        )
