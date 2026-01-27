from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings


class Role(models.Model):
    """User roles for RBAC (Role-Based Access Control).

    Standard roles: admin, assistant, doctor, billing, nurse
    """

    name = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="Name")
    label = models.CharField(max_length=128, verbose_name="Bezeichnung")

    class Meta:
        db_table = 'core_role'
        ordering = ['name']
        verbose_name = 'Rolle'
        verbose_name_plural = 'Rollen'

    def __str__(self) -> str:
        return self.label


class User(AbstractUser):
    """Custom User model with role-based access control.

    Extends Django's AbstractUser with:
    - role: ForeignKey to Role for RBAC
    - calendar_color: Hex color for calendar display
    - email: Made unique (required for JWT auth)
    """

    email = models.EmailField('E-Mail-Adresse', blank=True, unique=True)
    calendar_color = models.CharField(max_length=7, blank=True, default='#1E90FF', verbose_name="Kalenderfarbe")
    vacation_days_per_year = models.PositiveIntegerField(default=30, verbose_name="Urlaubstage pro Jahr")
    role = models.ForeignKey(
        Role,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name='users',
        verbose_name="Rolle",
    )

    class Meta:
        db_table = 'core_user'
        ordering = ['username']
        verbose_name = 'Benutzer'
        verbose_name_plural = 'Benutzer'


class AuditLog(models.Model):
    """Audit log for patient-related actions.

    Tracks who accessed/modified patient data and when.
    patient_id is stored as IntegerField (not FK) per dual-DB architecture.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name="Benutzer",
    )
    role_name = models.CharField(max_length=50, db_index=True, verbose_name="Rollenname")
    action = models.CharField(max_length=50, db_index=True, verbose_name="Aktion")
    patient_id = models.IntegerField(null=True, blank=True, db_index=True, verbose_name="Patient-ID")
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="Zeitstempel")
    meta = models.JSONField(null=True, blank=True, verbose_name="Metadaten")

    class Meta:
        db_table = 'core_auditlog'
        ordering = ['-timestamp', '-id']
        verbose_name = 'Audit-Protokoll'
        verbose_name_plural = 'Audit-Protokolle'
        indexes = [
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['patient_id', 'timestamp']),
        ]

    def __str__(self) -> str:
        return f"{self.timestamp} {self.action} (patient_id={self.patient_id})"

