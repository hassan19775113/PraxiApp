"""
Dashboard URL Configuration
"""
from django.urls import path

from .views import DashboardView, DashboardAPIView
from .scheduling_views import SchedulingDashboardView, SchedulingAPIView
from .appointment_calendar_views import (
    AppointmentCalendarDayView,
    AppointmentCalendarWeekView,
    AppointmentCalendarMonthView,
)
from .appointment_calendar_fullcalendar_view import AppointmentCalendarFullCalendarView
from .patient_views import (
    PatientDashboardView,
    PatientAPIView,
    PatientOverviewView,
    PatientDocumentDetailView,
    PatientPrescriptionDetailView,
    PatientDocumentUploadView,
    PatientNoteCreateView,
)
from .doctor_views import DoctorDashboardView, DoctorAPIView
from .operations_views import OperationsDashboardView, OperationsAPIView
from .resources_views import ResourcesDashboardView

app_name = 'dashboard'

urlpatterns = [
    # Haupt-Dashboard
    path('', DashboardView.as_view(), name='index'),
    path('api/', DashboardAPIView.as_view(), name='api'),
    
    # Scheduling Dashboard
    path('scheduling/', SchedulingDashboardView.as_view(), name='scheduling'),
    path('scheduling/api/', SchedulingAPIView.as_view(), name='scheduling_api'),

    # Termine (Kalenderansicht) - Neue FullCalendar-Integration
    path('appointments/', AppointmentCalendarFullCalendarView.as_view(), name='appointments_calendar'),
    path('appointments/fullcalendar/', AppointmentCalendarFullCalendarView.as_view(), name='appointments_calendar_fullcalendar'),
    # Legacy-Kalenderansichten (falls noch benötigt)
    path('appointments/legacy/day/', AppointmentCalendarDayView.as_view(), name='appointments_calendar_day_legacy'),
    path('appointments/legacy/week/', AppointmentCalendarWeekView.as_view(), name='appointments_calendar_week_legacy'),
    path('appointments/legacy/month/', AppointmentCalendarMonthView.as_view(), name='appointments_calendar_month_legacy'),
    
    # Patienten Dashboard
    path('patients/', PatientOverviewView.as_view(), name='patients'),  # Patientenliste
    path('patients/overview/', PatientOverviewView.as_view(), name='patients_overview'),  # Alias
    path('patients/<int:patient_id>/', PatientDashboardView.as_view(), name='patient_detail'),  # Detail-Ansicht
    path(
        'patients/<int:patient_id>/documents/<int:doc_id>/',
        PatientDocumentDetailView.as_view(),
        name='patient_document_detail',
    ),
    path(
        'patients/<int:patient_id>/documents/upload/',
        PatientDocumentUploadView.as_view(),
        name='patient_document_upload',
    ),
    path(
        'patients/<int:patient_id>/notes/create/',
        PatientNoteCreateView.as_view(),
        name='patient_note_create',
    ),
    path(
        'patients/<int:patient_id>/prescriptions/<int:prescription_id>/',
        PatientPrescriptionDetailView.as_view(),
        name='patient_prescription_detail',
    ),
    path('patients/api/', PatientAPIView.as_view(), name='patients_api'),
    path('patients/api/<int:patient_id>/', PatientAPIView.as_view(), name='patient_api_detail'),
    
    # Ärzte Dashboard
    path('doctors/', DoctorDashboardView.as_view(), name='doctors'),
    path('doctors/<int:doctor_id>/', DoctorDashboardView.as_view(), name='doctor_detail'),
    path('doctors/api/', DoctorAPIView.as_view(), name='doctors_api'),
    path('doctors/api/<int:doctor_id>/', DoctorAPIView.as_view(), name='doctor_api_detail'),
    
    # Operations Dashboard
    path('operations/', OperationsDashboardView.as_view(), name='operations'),
    path('operations/api/', OperationsAPIView.as_view(), name='operations_api'),
    
    # Ressourcen & Räume
    path('resources/', ResourcesDashboardView.as_view(), name='resources'),
]
