from praxi_backend.patients.models import Patient
from praxi_backend.patients.services import create_patient, update_patient
from praxi_backend.patients.validators import (
    validate_birth_date_not_future,
    validate_email_format,
    validate_patient_pk,
    validate_phone_format,
)
from rest_framework import serializers


class PatientReadSerializer(serializers.ModelSerializer):
    """Read-only serializer with all fields."""

    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "phone",
            "email",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class PatientWriteSerializer(serializers.ModelSerializer):
    """Write serializer for create/update operations."""

    # Legacy schema uses a manually managed PK, so we must accept it explicitly.
    id = serializers.IntegerField(write_only=True, required=True)

    class Meta:
        model = Patient
        fields = [
            "id",
            "first_name",
            "last_name",
            "birth_date",
            "gender",
            "phone",
            "email",
        ]

    def validate_id(self, value):
        """Ensure the patient primary key (legacy patient_id) is positive."""
        return validate_patient_pk(value)

    def validate_birth_date(self, value):
        return validate_birth_date_not_future(value)

    def validate_email(self, value):
        try:
            return validate_email_format(value)
        except Exception:
            raise serializers.ValidationError("Invalid email address.")

    def validate_phone(self, value):
        return validate_phone_format(value)

    def create(self, validated_data):
        """Create patient using the default database."""
        return create_patient(data=validated_data)

    def update(self, instance, validated_data):
        """Update patient using the default database."""
        return update_patient(instance=instance, data=validated_data)
