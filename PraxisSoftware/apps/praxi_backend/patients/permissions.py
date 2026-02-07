from praxi_backend.core.permissions import RBACPermission
from rest_framework.permissions import SAFE_METHODS


class PatientPermission(RBACPermission):
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

    # Preserve legacy behavior: staff/superuser act as admin.
    treat_staff_as_admin = True
    treat_superuser_as_admin = True

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if not role_name:
            return False

        # Billing can only read.
        if role_name == "billing" and request.method not in SAFE_METHODS:
            return False

        return True
