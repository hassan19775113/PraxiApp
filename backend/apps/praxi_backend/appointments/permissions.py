from praxi_backend.core.permissions import RBACPermission
from rest_framework.permissions import SAFE_METHODS


class AppointmentPermission(RBACPermission):
    """RBAC für Termine.

    - admin: alles
    - assistant: alles
    - doctor: nur eigene Termine (read/write)
    - billing: nur read
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant", "doctor"}

    # Preserve legacy behavior: staff/superuser act as admin for appointments.
    treat_staff_as_admin = True
    treat_superuser_as_admin = True

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if not role_name:
            return False

        if role_name == "billing" and request.method not in SAFE_METHODS:
            return False

        if role_name == "doctor":
            return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)

        return True


class AppointmentTypePermission(RBACPermission):
    """RBAC für Termin-Typen.

    - admin: alle Rechte
    - assistant: nur GET
    - doctor: nur GET
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin"}


class PracticeHoursPermission(RBACPermission):
    """RBAC für Praxis-Arbeitszeiten.

    - admin: alle Rechte
    - assistant: alle Rechte
    - doctor: nur GET
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}


class ResourcePermission(RBACPermission):
    """RBAC für Ressourcen (Räume & Geräte).

    - admin: alle Rechte
    - assistant: alle Rechte
    - doctor: nur GET
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}


class DoctorHoursPermission(RBACPermission):
    """RBAC für Arzt-Sprechzeiten.

    - admin: alle Rechte
    - assistant: alle Rechte
    - doctor: nur GET (nur eigene DoctorHours)
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if role_name == "doctor":
            return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)
        return True


class DoctorAbsencePermission(RBACPermission):
    """RBAC für Arzt-Abwesenheiten.

    - admin: alle Rechte
    - assistant: alle Rechte
    - doctor: nur GET/PUT/PATCH/DELETE für eigene Abwesenheiten (kein POST)
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}

    def has_permission(self, request, view):
        # Preserve legacy behavior:
        # - SAFE_METHODS: role-based read
        # - doctor: may update/delete (no POST)
        # - billing: read-only (no write)
        if not self._is_authenticated(request):
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method in SAFE_METHODS:
            return role_name in self.read_roles

        if role_name == "doctor":
            return request.method in ("PUT", "PATCH", "DELETE")

        return role_name in self.write_roles

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if request.method in SAFE_METHODS:
            if role_name == "doctor":
                return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)
            return True

        if role_name == "billing":
            return False

        if role_name == "doctor":
            return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)

        return True


class DoctorBreakPermission(RBACPermission):
    """RBAC für Pausen/Blockzeiten.

    - admin: alle Rechte
    - assistant: alle Rechte
    - doctor: nur GET/PUT/PATCH/DELETE für eigene Pausen (doctor=request.user)
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}

    def has_permission(self, request, view):
        # Preserve legacy behavior:
        # - SAFE_METHODS: role-based read
        # - doctor: may update/delete (no POST)
        if not self._is_authenticated(request):
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method in SAFE_METHODS:
            return role_name in self.read_roles

        if role_name == "doctor":
            return request.method in ("PUT", "PATCH", "DELETE")

        return role_name in self.write_roles

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if request.method in SAFE_METHODS:
            if role_name == "doctor":
                return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)
            return True

        if role_name == "billing":
            return False

        if role_name == "doctor":
            return getattr(obj, "doctor_id", None) == getattr(request.user, "id", None)

        return True


class AppointmentSuggestPermission(RBACPermission):
    """RBAC für Terminvorschläge.

    - admin/assistant: erlaubt
    - doctor: nur für sich selbst (doctor_id query param)
    - billing: nur GET (für alle Ärzte)
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not self._is_authenticated(request):
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method not in SAFE_METHODS:
            return False

        if role_name not in self.read_roles:
            return False

        # Doctors may only request suggestions for themselves.
        if role_name == "doctor":
            doctor_id = request.query_params.get("doctor_id")
            if not doctor_id:
                return False
            try:
                return int(doctor_id) == int(getattr(user, "id", 0) or 0)
            except (TypeError, ValueError):
                return False

        return True


class OperationPermission(RBACPermission):
    """RBAC für Operationen.

    - admin: CRUD
    - assistant: CRUD
    - doctor: read-only, nur eigene OPs (Teammitglied)
    - billing: read-only
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method not in SAFE_METHODS:
            return role_name in self.write_roles

        if role_name != "doctor":
            return True

        user_id = getattr(request.user, "id", None)
        return user_id in {
            getattr(obj, "primary_surgeon_id", None),
            getattr(obj, "assistant_id", None),
            getattr(obj, "anesthesist_id", None),
        }


class OperationTypePermission(RBACPermission):
    """RBAC für OP-Typen.

    - admin: CRUD
    - assistant/doctor/billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin"}


class OperationSuggestPermission(RBACPermission):
    """RBAC für OP-Vorschläge.

    - admin/assistant: erlaubt
    - doctor: nur für sich selbst (primary_surgeon_id query param)
    - billing: erlaubt (read-only Rolle)
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}

    def has_permission(self, request, view):
        user = getattr(request, "user", None)
        if not self._is_authenticated(request):
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method not in SAFE_METHODS:
            return False

        if role_name not in self.read_roles:
            return False

        if role_name == "doctor":
            surgeon_id = request.query_params.get("primary_surgeon_id")
            if not surgeon_id:
                return False
            try:
                return int(surgeon_id) == int(getattr(user, "id", 0) or 0)
            except (TypeError, ValueError):
                return False

        return True


class OpDashboardPermission(RBACPermission):
    """RBAC für OP-Dashboard Endpoints.

    - admin/assistant: GET + PATCH
    - doctor: nur GET
    - billing: nur GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant"}


class OpStatsPermission(RBACPermission):
    """RBAC für OP-Statistik Endpoints.

    - admin/assistant: alle Endpoints
    - billing: read-only für alle Endpoints
    - doctor: nur /overview/ und /surgeons/ (jeweils nur eigene OPs)
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    doctor_scopes = {"overview", "surgeons"}

    def has_permission(self, request, view):
        if not self._is_authenticated(request):
            return False

        role_name = self._role_name(request)
        if not role_name:
            return False

        if request.method not in SAFE_METHODS:
            return False

        if role_name not in self.read_roles:
            return False

        scope = getattr(view, "stats_scope", None)
        if role_name == "doctor":
            return scope in self.doctor_scopes

        return True


class OpTimelinePermission(RBACPermission):
    """RBAC für OP-Timeline Endpoints.

    - admin/assistant: alle Timeline Endpoints (GET)
    - doctor: Timeline (GET), Sichtbarkeit wird zusätzlich in Views gefiltert
    - billing: read-only (GET)
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}

    # Read-only endpoint.
    write_roles = set()


class ResourceCalendarPermission(RBACPermission):
    """RBAC für Ressourcen-Kalender Endpoints.

    - admin/assistant: GET
    - doctor: GET (Sichtbarkeit wird zusätzlich in Views gefiltert)
    - billing: GET
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}

    # Read-only endpoint.
    write_roles = set()


class PatientFlowPermission(RBACPermission):
    """RBAC für PatientFlow/Wartezimmer.

    - admin/assistant: alle Endpoints
    - doctor: nur eigene Flows (zugeordnet über Termin/OP)
    - billing: read-only
    """

    read_roles = {"admin", "assistant", "doctor", "billing"}
    write_roles = {"admin", "assistant", "doctor"}

    def has_object_permission(self, request, view, obj):
        role_name = self._role_name(request)
        if not role_name:
            return False

        # doctor: only flows assigned via appointment/operation
        if role_name == "doctor":
            uid = getattr(getattr(request, "user", None), "id", None)
            appt = getattr(obj, "appointment", None)
            if appt is not None and getattr(appt, "doctor_id", None) == uid:
                return True
            op = getattr(obj, "operation", None)
            if op is not None and uid is not None:
                if getattr(op, "primary_surgeon_id", None) == uid:
                    return True
                if getattr(op, "assistant_id", None) == uid:
                    return True
                if getattr(op, "anesthesist_id", None) == uid:
                    return True
            return False

        # done is read-only for everyone
        if request.method not in SAFE_METHODS and getattr(obj, "status", None) == "done":
            return False

        if request.method in SAFE_METHODS:
            return True

        if role_name == "billing":
            return False

        return True
