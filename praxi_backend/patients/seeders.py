import random
from datetime import date, datetime, timedelta

from django.db import transaction

from praxi_backend.patients.models import Patient

RANDOM_SEED = 42


def seed_patients() -> dict:
    """Seed managed patients.

    Safety behavior:
    - never deletes existing patients
    - creates demo patients only when the table is empty

    This keeps production safer while still allowing `seed` to work in DEV.
    """

    random.seed(RANDOM_SEED)
    stats: dict[str, int] = {"patients_patients": 0}

    try:
        if Patient.objects.using("default").exists():
            return stats
    except Exception:
        # Table may not exist yet.
        return stats

    with transaction.atomic(using="default"):
        patients = _seed_patients()
        stats["patients_patients"] = len(patients)

    return stats


def _seed_patients() -> list[Patient]:
    first_names_male = ["Ali", "Omar", "Karim", "Hassan", "Yusuf", "Mahmoud"]
    first_names_female = ["Sara", "Layla", "Mariam", "Amina", "Noura", "Fatima"]
    last_names = ["Ahmad", "Salim", "Jabari", "Haddad", "Khalil", "Rahman", "Hamidi", "Faruq"]

    patients: list[Patient] = []

    base_date = date.today()

    # Ensure stable integer PKs.
    try:
        last_id = (
            Patient.objects.using("default").order_by("-id").values_list("id", flat=True).first()
        )
        start_id = int(last_id or 0) + 1
    except Exception:
        start_id = 1

    for i in range(20):
        if random.random() < 0.5:
            first_name = random.choice(first_names_male)
            gender = "male"
        else:
            first_name = random.choice(first_names_female)
            gender = "female"

        last_name = random.choice(last_names)
        birth_year = random.randint(1940, 2010)
        birth_month = random.randint(1, 12)
        birth_day = random.randint(1, 28)
        birth_date = date(birth_year, birth_month, birth_day)

        phone = f"+49 170 {random.randint(1000000, 9999999)}"
        email = f"{first_name.lower()}.{last_name.lower()}@example.com"

        created_at = datetime.combine(
            base_date - timedelta(days=random.randint(0, 365)),
            datetime.min.time(),
        )
        updated_at = created_at + timedelta(days=random.randint(0, 60))

        patient = Patient.objects.using("default").create(
            id=start_id + i,
            first_name=first_name,
            last_name=last_name,
            birth_date=birth_date,
            gender=gender,
            phone=phone,
            email=email,
            created_at=created_at,
            updated_at=updated_at,
        )
        patients.append(patient)

    return patients
