from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("patients", "0004_patientnote"),
    ]

    operations = [
        migrations.AddField(
            model_name="patientnote",
            name="author_role",
            field=models.CharField(blank=True, max_length=255),
        ),
    ]
