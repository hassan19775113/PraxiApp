from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_alter_auditlog_options_alter_role_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="vacation_days_per_year",
            field=models.PositiveIntegerField(default=30, verbose_name="Urlaubstage pro Jahr"),
        ),
    ]
