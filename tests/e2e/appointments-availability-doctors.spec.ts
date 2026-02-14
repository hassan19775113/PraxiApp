import { test, expect } from '../fixtures/testdata.setup';
import { CalendarPage } from '../pages/calendar-page';
import { AppointmentModalPage } from '../pages/appointment-modal-page';

type Slot = { date: string; start: string; end: string };

function fmtDateLocal(d: Date): string {
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${y}-${m}-${day}`;
}

function addDays(base: Date, days: number): Date {
  const d = new Date(base);
  d.setDate(d.getDate() + days);
  return d;
}

async function findSlotWithAvailableDoctors(page: import('@playwright/test').Page): Promise<Slot | null> {
  return page.evaluate(async () => {
    const pad = (n: number) => String(n).padStart(2, '0');
    const fmtDate = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;

    const now = new Date();
    for (let dayOffset = 0; dayOffset <= 14; dayOffset++) {
      const current = new Date(now);
      current.setDate(now.getDate() + dayOffset);
      const date = fmtDate(current);

      for (const hour of [9, 10, 11, 13, 14]) {
        const start = `${pad(hour)}:00`;
        const end = `${pad(hour)}:30`;

        const startIso = `${date}T${start}:00`;
        const endIso = `${date}T${end}:00`;
        const url = `/api/availability/?start=${encodeURIComponent(startIso)}&end=${encodeURIComponent(endIso)}`;

        const response = await fetch(url, {
          headers: { Accept: 'application/json' },
          credentials: 'same-origin',
        });

        if (!response.ok) continue;
        const data = await response.json();
        const doctors = Array.isArray(data?.available_doctors) ? data.available_doctors : [];
        if (doctors.length > 0) {
          return { date, start, end };
        }
      }
    }

    return null;
  });
}

test('availability modal keeps doctors when slot has available doctors', async ({ page, baseURL }) => {
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

  const slot = await findSlotWithAvailableDoctors(page);
  expect(slot, 'No slot with available doctors found in the next 14 days').not.toBeNull();

  const availabilityResponse = await modal.updateTimesAndWaitForAvailability(
    slot!.date,
    slot!.start,
    slot!.end
  );

  expect(availabilityResponse.ok()).toBeTruthy();
  const payload = await availabilityResponse.json();
  const apiDoctors = Array.isArray(payload?.available_doctors) ? payload.available_doctors.length : 0;
  expect(apiDoctors).toBeGreaterThan(0);

  await expect
    .poll(async () => await modal.doctorSelect.locator('option').count(), {
      timeout: 10_000,
      message: 'Doctor dropdown should contain at least one selectable doctor after availability update',
    })
    .toBeGreaterThan(1);
});
