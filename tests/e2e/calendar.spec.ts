import { test, expect } from '@playwright/test';
import { CalendarPage } from '../pages/calendar-page';
import { AppointmentModalPage } from '../pages/appointment-modal-page';
import { ApiClient } from '../../api-client';

// Calendar E2E: dynamically choose available doctor/type/patient from live options, create appointment, assert card.
test('create appointment via calendar modal with live options', async ({ page, baseURL }) => {
  const calendar = new CalendarPage(page);
  const modal = new AppointmentModalPage(page);

  let createdAppointmentId: number | string | null = null;

  await calendar.goto(baseURL!);

  try {
    // Open creation modal.
    await calendar.openNewAppointment();
    await modal.expectOpen();

    await modal.waitForDropdownsLoaded();
    const { titleLabel: modalTitleLabel } = await modal.getFirstSelectableLabels();

    const today = new Date();
    const yyyy = today.getFullYear();
    const mm = String(today.getMonth() + 1).padStart(2, '0');
    const dd = String(today.getDate()).padStart(2, '0');
    const date = `${yyyy}-${mm}-${dd}`;

    // Pick a window and then choose doctor/patient from the availability response.
    const start = '09:00';
    const end = '09:30';
    const availabilityResponse = await modal.updateTimesAndWaitForAvailability(date, start, end);
    if (!availabilityResponse.ok()) {
      const body = await availabilityResponse.text();
      throw new Error(
        `UI availability check failed: ${availabilityResponse.status()} ${availabilityResponse.statusText()} - ${body}`
      );
    }

    const availability = (await availabilityResponse.json()) as any;
    const firstDoctorId = availability?.available_doctors?.[0]?.id;
    const firstPatientId = availability?.available_patients?.[0]?.id;

    if (!firstDoctorId || !firstPatientId) {
      test.skip(true, 'No available doctor/patient for 09:00-09:30 window');
      return;
    }

    await modal.titleSelect.selectOption({ label: String(modalTitleLabel) });
    await modal.doctorSelect.selectOption({ value: String(firstDoctorId) });
    await modal.patientSelect.selectOption({ value: String(firstPatientId) });
    await modal.descriptionInput.fill('E2E Termin via Playwright');

    const saveResponse = await modal.saveAndWaitForAppointmentsMutation(15_000);
    if (!saveResponse.ok()) {
      const body = await saveResponse.text();
      throw new Error(`Create appointment failed: ${saveResponse.status()} ${saveResponse.statusText()} - ${body}`);
    }
    const created = (await saveResponse.json()) as any;
    createdAppointmentId = created?.id ?? created?.pk;
    expect(createdAppointmentId).toBeTruthy();

    // Assert by appointment id (stable; card text does not include notes).
    await expect(calendar.appointmentCardById(createdAppointmentId!)).toBeVisible();
  } finally {
    // Best-effort cleanup to keep DB stable across runs.
    if (createdAppointmentId) {
      try {
        const api = new ApiClient();
        await api.init();
        await api.deleteAppointment(createdAppointmentId);
        await api.dispose();
      } catch {
        // ignore cleanup errors
      }
    }
  }
});
