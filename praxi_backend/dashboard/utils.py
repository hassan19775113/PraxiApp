"""
Utility functions for dashboard views.
"""

from typing import Dict

from praxi_backend.patients.models import Patient


def get_patient_display_name(patient_id: int) -> str:
    """
    Holt den Anzeigenamen eines Patienten (Name, Geburtsdatum).
    
    Nutzt die managed Patienten-Tabelle (default DB).
    Falls nicht gefunden, gibt "Patient #ID" zurück.
    
    Args:
        patient_id: Die Patient-ID
        
    Returns:
        Anzeigename im Format "Nachname, Vorname (Geburtsdatum)" oder "Patient #ID"
    """
    try:
        patient = Patient.objects.using('default').get(id=patient_id)
        birth_str = patient.birth_date.strftime('%d.%m.%Y') if patient.birth_date else ''
        name = f"{patient.last_name}, {patient.first_name}"
        if birth_str:
            name += f" ({birth_str})"
        return name
    except Patient.DoesNotExist:
        pass
    except Exception:
        pass
    
    # Fallback
    return f"Patient #{patient_id}"


def get_patient_names_batch(patient_ids: list[int]) -> Dict[int, str]:
    """
    Holt Anzeigenamen für mehrere Patienten (Batch-Lookup).
    
    Args:
        patient_ids: Liste von Patient-IDs
        
    Returns:
        Dictionary: {patient_id: display_name}
    """
    result: Dict[int, str] = {}
    
    if not patient_ids:
        return result
    
    try:
        patients = Patient.objects.using('default').filter(id__in=patient_ids)
        for patient in patients:
            birth_str = patient.birth_date.strftime('%d.%m.%Y') if patient.birth_date else ''
            name = f"{patient.last_name}, {patient.first_name}"
            if birth_str:
                name += f" ({birth_str})"
            result[patient.id] = name
    except Exception:
        pass
    
    # Fallbacks für nicht gefundene
    for pid in patient_ids:
        if pid not in result:
            result[pid] = f"Patient #{pid}"
    
    return result

