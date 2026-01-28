"""Patients App URLs.

Prefix: /api/
Routes:
    GET/POST    /api/patients/            - List/Create patients
    GET/PUT     /api/patients/<pk>/       - Retrieve/Update patient
    GET         /api/patients/search/?q=  - Lightweight search for UI autocompletes
"""

from django.urls import path

from praxi_backend.patients.views import (
    PatientListCreateView,
    PatientSearchView,
    PatientRetrieveUpdateView,
)

app_name = 'patients'

urlpatterns = [
    path('patients/', PatientListCreateView.as_view(), name='list'),
    path('patients/search/', PatientSearchView.as_view(), name='search'),
    path('patients/<int:pk>/', PatientRetrieveUpdateView.as_view(), name='detail'),
]
