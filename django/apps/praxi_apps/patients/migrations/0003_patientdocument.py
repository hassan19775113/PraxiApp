from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0002_rename_table_to_patients_cache"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientDocument",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("patient_id", models.IntegerField(db_index=True)),
                ("title", models.CharField(max_length=255)),
                (
                    "doc_type",
                    models.CharField(
                        choices=[("document", "Dokument"), ("report", "Bericht")], max_length=20
                    ),
                ),
                (
                    "file",
                    models.FileField(blank=True, null=True, upload_to="patient_documents/%Y/%m/%d"),
                ),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "patient_documents",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
