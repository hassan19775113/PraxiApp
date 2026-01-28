from __future__ import annotations

from django.db import models


class Patient(models.Model):
    """Managed patient master record in the *default* database.

    This replaces the former dual-DB setup and becomes the single source of truth
    for patients.

    The schema mirrors the former legacy table ``patients``.

    Notes about ID stability:
    - Existing domain models (appointments/operations) store ``patient_id`` as an
      integer.
    - Therefore, we use the legacy patient ID as the primary key here.
    """

    # Legacy ID becomes the primary key to keep references stable.
    id = models.IntegerField(primary_key=True)

    first_name = models.CharField(max_length=100, blank=True, default="")
    last_name = models.CharField(max_length=100, blank=True, default="")
    birth_date = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)

    phone = models.CharField(max_length=50, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True)

    # Keep legacy timestamps; allow NULL for robustness across imports.
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "patients"
        ordering = ["last_name", "first_name", "id"]
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self) -> str:
        name = f"{self.last_name}, {self.first_name}".strip(", ")
        return name or f"Patient {self.id}"


class PatientDocument(models.Model):
    """Patient documents (upload/note) in the default DB."""

    DOC_TYPE_DOCUMENT = "document"
    DOC_TYPE_REPORT = "report"
    DOC_TYPE_CHOICES = [
        (DOC_TYPE_DOCUMENT, "Dokument"),
        (DOC_TYPE_REPORT, "Bericht"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="documents",
        db_column="patient_id",
    )
    title = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES)
    file = models.FileField(upload_to="patient_documents/%Y/%m/%d", null=True, blank=True)
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_documents"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.title} (patient_id={self.patient_id})"


class PatientNote(models.Model):
    """Notizen der Aerzte zu einem Patienten (lokal, Default-DB)."""

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="notes",
        db_column="patient_id",
    )
    author_name = models.CharField(max_length=255, blank=True)
    author_role = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "patient_notes"
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"Note(patient_id={self.patient_id}, author={self.author_name or 'Unbekannt'})"


# NOTE: The former cache table (patients_cache) is removed via migrations.
# If you still have legacy/cached data, use the management command:
#
#   python manage.py migrate_patients_from_legacy
