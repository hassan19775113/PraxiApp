import { Page, expect } from '@playwright/test';

// Page Object: Header navigation (base_dashboard.html)
// Uses getByRole('link', { name }) for real labels: Dashboards, Terminplanung, Patienten,
// Ärzte, Operationen, Ressourcen, Admin
// Dependency: rendered dashboard header (authenticated session)
export class NavPage {
  constructor(private readonly page: Page) {}

  async gotoDashboards() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/?/),
      this.page.getByRole('link', { name: 'Dashboards', exact: true }).click(),
    ]);
  }

  async gotoScheduling() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/appointments\/?/),
      this.page.getByRole('link', { name: 'Terminplanung', exact: true }).click(),
    ]);
  }

  async gotoPatients() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/patients\/?/),
      this.page.getByRole('link', { name: 'Patienten', exact: true }).click(),
    ]);
  }

  async gotoDoctors() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/doctors\/?/),
      this.page.getByRole('link', { name: 'Ärzte', exact: true }).click(),
    ]);
  }

  async gotoOperations() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/operations\/?/),
      this.page.getByRole('link', { name: 'Operationen', exact: true }).click(),
    ]);
  }

  async gotoResources() {
    await Promise.all([
      this.page.waitForURL(/\/praxi_backend\/dashboard\/resources\/?/),
      this.page.getByRole('link', { name: 'Ressourcen', exact: true }).click(),
    ]);
  }

  async gotoAdmin() {
    await this.page.getByRole('link', { name: 'Admin', exact: true }).click();
  }

  async expectHeaderVisible() {
    await expect(this.page.getByRole('navigation')).toBeVisible();
  }
}
