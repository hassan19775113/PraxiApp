from rest_framework.permissions import BasePermission, SAFE_METHODS


class PatientPermission(BasePermission):
    """RBAC for Patient endpoints.

    Current domain model has no explicit patient ownership/assignment relation.
    Therefore RBAC is role-based only:
    - admin: full access
    - assistant: full access
    - doctor: full access
    - billing: read-only
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant", "doctor"}

    def _role_name(self, request):
        user = getattr(request, "user", None)
        if user and (getattr(user, "is_superuser", False) or getattr(user, "is_staff", False)):
            return "admin"
        role = getattr(user, "role", None)
        return getattr(role, "name", None)

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method in SAFE_METHODS:
            return role_name in self.read_roles

        return role_name in self.write_roles

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if not role_name:
            return False

        # Billing can only read.
        if role_name == "billing" and request.method not in SAFE_METHODS:
            return False

        return True
