import { test } from '../fixtures/testdata.setup';
import { SchedulingKpisPage } from '../pages/scheduling-kpis-page';

// Validate KPI charts render (presence of canvases/funnel container).
test('scheduling KPIs show charts', async ({ page, baseURL, testData }) => {
  if (!testData.appointmentId || !testData.doctorId || !testData.patientId) {
    test.skip(true, 'Scheduling KPI seed data is missing; skipping chart visibility assertions');
  }

  const scheduling = new SchedulingKpisPage(page);
  await scheduling.goto(baseURL!);
  if (page.url().includes('/login')) {
    test.skip(true, 'Not authenticated in scheduling KPI test environment');
    return;
  }
  await scheduling.expectChartsVisible();
});
