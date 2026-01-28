from rest_framework import serializers

from praxi_backend.patients.models import Patient


class PatientReadSerializer(serializers.ModelSerializer):
    """Read-only serializer with all fields."""

    class Meta:
        model = Patient
        fields = [
            'id',
            'first_name',
            'last_name',
            'birth_date',
            'gender',
            'phone',
            'email',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class PatientWriteSerializer(serializers.ModelSerializer):
    """Write serializer for create/update operations."""

    class Meta:
        model = Patient
        fields = [
            'id',
            'first_name',
            'last_name',
            'birth_date',
            'gender',
            'phone',
            'email',
        ]

    def validate_id(self, value):
        """Ensure the patient primary key (legacy patient_id) is positive."""
        if value is None or value <= 0:
            raise serializers.ValidationError('id must be a positive integer.')
        return value

    def create(self, validated_data):
        """Create patient using the default database."""
        return Patient.objects.using('default').create(**validated_data)

    def update(self, instance, validated_data):
        """Update patient using the default database."""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save(using='default')
        return instance
