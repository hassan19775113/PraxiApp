"""Central validators for the core app.

Keep validation logic here so serializers/views stay small and consistent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from praxi_backend.core.models import User
from rest_framework import serializers

if TYPE_CHECKING:
    from praxi_backend.core.models import User as UserModel


def validate_role_name(value: str) -> str:
    """Validate and normalize a Role.name.

    Rules:
    - required
    - lowercase
    - alphanumeric with underscores
    """
    if value is None:
        raise serializers.ValidationError("name is required.")
    value = str(value).strip()
    if not value:
        raise serializers.ValidationError("name is required.")
    normalized = value.lower()
    if not normalized.replace("_", "").isalnum():
        raise serializers.ValidationError("name must be alphanumeric with underscores only.")
    return normalized


def validate_unique_user_email(value: str, *, instance: UserModel | None = None) -> str:
    """Validate that a user email is unique on the default DB.

    If instance is provided, it is excluded (update case).
    """
    if value is None:
        return value
    value = str(value).strip()
    if not value:
        return value

    qs = User.objects.using("default").filter(email=value)
    if instance is not None:
        qs = qs.exclude(pk=instance.pk)
    if qs.exists():
        raise serializers.ValidationError("A user with this email already exists.")
    return value


def validate_old_password(value: str, *, user: UserModel | None) -> str:
    """Validate that the provided old password matches the given user."""
    if user is None or not user.check_password(value):
        raise serializers.ValidationError("Current password is incorrect.")
    return value
