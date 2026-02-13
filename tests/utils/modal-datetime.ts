import { Page } from '@playwright/test';

function pad2(n: number) {
  return String(n).padStart(2, '0');
}

/**
 * Convert ISO datetimes into the calendar modal's expected local input strings.
 *
 * Important: compute this inside the browser context to avoid Node/browser
 * timezone mismatches.
 */
export async function toModalDateTimeInputsInBrowser(
  page: Page,
  isoStart: string,
  isoEnd: string
): Promise<{ dateStr: string; startStr: string; endStr: string }> {
  return page.evaluate(
    ({ isoStart, isoEnd }) => {
      const pad2Inner = (n: number) => String(n).padStart(2, '0');
      const start = new Date(isoStart);
      const end = new Date(isoEnd);

      const dateStr = `${start.getFullYear()}-${pad2Inner(start.getMonth() + 1)}-${pad2Inner(start.getDate())}`;
      const startStr = `${pad2Inner(start.getHours())}:${pad2Inner(start.getMinutes())}`;
      const endStr = `${pad2Inner(end.getHours())}:${pad2Inner(end.getMinutes())}`;

      return { dateStr, startStr, endStr };
    },
    { isoStart, isoEnd }
  );
}
