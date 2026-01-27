"""
Utility functions for dashboard views.
"""

from typing import Dict, Optional

from praxi_backend.medical.models import Patient as MedicalPatient
from praxi_backend.patients.models import Patient as PatientCache


def get_patient_display_name(patient_id: int) -> str:
    """
    Holt den Anzeigenamen eines Patienten (Name, Geburtsdatum).
    
    Versucht zuerst die Legacy-DB (medical), dann den Cache (patients_cache).
    Falls nicht gefunden, gibt "Patient #ID" zurück.
    
    Args:
        patient_id: Die Patient-ID
        
    Returns:
        Anzeigename im Format "Nachname, Vorname (Geburtsdatum)" oder "Patient #ID"
    """
    # Versuche Legacy-DB
    try:
        patient = MedicalPatient.objects.using('medical').get(id=patient_id)
        birth_str = patient.birth_date.strftime('%d.%m.%Y') if patient.birth_date else ''
        name = f"{patient.last_name}, {patient.first_name}"
        if birth_str:
            name += f" ({birth_str})"
        return name
    except MedicalPatient.DoesNotExist:
        pass
    except Exception:
        # DB nicht verfügbar (z.B. DEV ohne Legacy-DB)
        pass
    
    # Versuche Cache
    try:
        cached = PatientCache.objects.using('default').filter(patient_id=patient_id).first()
        if cached:
            birth_str = cached.birth_date.strftime('%d.%m.%Y') if cached.birth_date else ''
            name = f"{cached.last_name}, {cached.first_name}"
            if birth_str:
                name += f" ({birth_str})"
            return name
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
    
    # Versuche Legacy-DB
    try:
        patients = MedicalPatient.objects.using('medical').filter(id__in=patient_ids)
        for patient in patients:
            birth_str = patient.birth_date.strftime('%d.%m.%Y') if patient.birth_date else ''
            name = f"{patient.last_name}, {patient.first_name}"
            if birth_str:
                name += f" ({birth_str})"
            result[patient.id] = name
    except Exception:
        pass
    
    # Fehlende aus Cache holen
    missing_ids = [pid for pid in patient_ids if pid not in result]
    if missing_ids:
        try:
            cached = PatientCache.objects.using('default').filter(patient_id__in=missing_ids)
            for patient in cached:
                birth_str = patient.birth_date.strftime('%d.%m.%Y') if patient.birth_date else ''
                name = f"{patient.last_name}, {patient.first_name}"
                if birth_str:
                    name += f" ({birth_str})"
                result[patient.patient_id] = name
        except Exception:
            pass
    
    # Fallbacks für nicht gefundene
    for pid in patient_ids:
        if pid not in result:
            result[pid] = f"Patient #{pid}"
    
    return result

