"""Service layer for the core app.

Business logic for auth/token issuance and small utility operations.
Views should only orchestrate request/response.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db import connection
from praxi_backend.core.serializers import RoleSerializer
from rest_framework_simplejwt.tokens import RefreshToken


@dataclass(frozen=True)
class DBHealth:
    ok: bool
    detail: str | None = None


def check_db_health() -> DBHealth:
    """Perform a simple DB query to ensure connectivity."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
        return DBHealth(ok=True)
    except Exception as exc:  # pragma: no cover (DB errors are environment-specific)
        return DBHealth(ok=False, detail=str(exc))


def issue_tokens_for_user(user) -> tuple[str, str]:
    """Issue (access, refresh) tokens and embed role claim into refresh token."""
    refresh = RefreshToken.for_user(user)
    role = getattr(user, "role", None)
    refresh["role"] = getattr(role, "name", None) if role else None
    access = refresh.access_token
    return str(access), str(refresh)


def build_login_user_payload(user) -> dict:
    """Build the user payload returned by the login endpoint."""
    role = getattr(user, "role", None)
    role_data = RoleSerializer(role).data if role else None
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": role_data,
    }


def build_login_response(user) -> dict:
    """Build the full response body for the login endpoint."""
    access, refresh = issue_tokens_for_user(user)
    return {
        "user": build_login_user_payload(user),
        "access": access,
        "refresh": refresh,
    }


def refresh_access_token(refresh_token: str) -> str:
    """Given a refresh token, return a new access token string."""
    token = RefreshToken(refresh_token)
    return str(token.access_token)
