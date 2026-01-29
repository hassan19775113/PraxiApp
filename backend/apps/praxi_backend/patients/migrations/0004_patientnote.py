from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0003_patientdocument"),
    ]

    operations = [
        migrations.CreateModel(
            name="PatientNote",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
                    ),
                ),
                ("patient_id", models.IntegerField(db_index=True)),
                ("author_name", models.CharField(blank=True, max_length=255)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "patient_notes",
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
