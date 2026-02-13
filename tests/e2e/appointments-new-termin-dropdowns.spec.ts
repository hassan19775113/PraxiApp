import { test, expect } from '../fixtures/testdata.setup';
import { CalendarPage } from '../pages/calendar-page';
import { AppointmentModalPage } from '../pages/appointment-modal-page';

test('neuer termin shows populated dropdowns for title, arzt, patient', async ({ page, baseURL }) => {
  const calendar = new CalendarPage(page);
  const modal = new AppointmentModalPage(page);

  await page.goto(`${baseURL}/praxi_backend/dashboard/appointments/`);
  await page.waitForLoadState('domcontentloaded');

  if (page.url().includes('/admin/login')) {
    throw new Error('Dashboard appointments page redirected to login; authentication/session missing');
  }

  await expect(calendar.appointmentCalendar).toBeVisible();

  await calendar.openNewAppointment();
  await modal.expectOpen();
  await modal.waitForDropdownsLoaded();

  const titleOptions = modal.titleSelect.locator('option');
  const doctorOptions = modal.doctorSelect.locator('option');
  const patientOptions = modal.patientSelect.locator('option');

  expect(await titleOptions.count()).toBeGreaterThan(1);
  expect(await doctorOptions.count()).toBeGreaterThan(1);
  expect(await patientOptions.count()).toBeGreaterThan(1);

  await expect(modal.titleSelect.locator('option', { hasText: 'Fehler beim Laden' })).toHaveCount(0);
  await expect(modal.doctorSelect.locator('option', { hasText: 'Fehler beim Laden' })).toHaveCount(0);
  await expect(modal.patientSelect.locator('option', { hasText: 'Fehler beim Laden' })).toHaveCount(0);

});
