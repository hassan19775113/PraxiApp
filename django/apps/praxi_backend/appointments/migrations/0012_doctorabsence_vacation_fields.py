from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("appointments", "0011_alter_appointment_options_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="doctorabsence",
            name="duration_workdays",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Dauer (Werktage)"
            ),
        ),
        migrations.AddField(
            model_name="doctorabsence",
            name="remaining_days",
            field=models.PositiveIntegerField(
                blank=True, null=True, verbose_name="Verbleibend (Urlaubstage)"
            ),
        ),
        migrations.AddField(
            model_name="doctorabsence",
            name="return_date",
            field=models.DateField(blank=True, null=True, verbose_name="Arbeitet wieder ab"),
        ),
    ]
