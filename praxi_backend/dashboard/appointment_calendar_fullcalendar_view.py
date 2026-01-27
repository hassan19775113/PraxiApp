"""
View für die moderne FullCalendar-Terminplanung.

Verwendet das neue FullCalendar-Template mit Drag & Drop.
"""
from django.views.generic import TemplateView


class AppointmentCalendarFullCalendarView(TemplateView):
    """
    Moderne FullCalendar-Terminplanung.
    
    Verwendet appointments_calendar_fullcalendar.html
    mit vollständiger FullCalendar-Integration.
    """
    template_name = 'dashboard/appointments_calendar_fullcalendar.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Terminplanung'
        return context

