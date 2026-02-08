#!/usr/bin/env node

import { request } from 'playwright';

const BASE_URL = process.env.BASE_URL || 'http://localhost:8000';
const E2E_USER = process.env.E2E_USER || 'e2e_ci';
const E2E_PASSWORD = process.env.E2E_PASSWORD || 'e2e_ci_pw';

async function login() {
  const api = await request.newContext({ baseURL: BASE_URL });
  let res = await api.post('/api/auth/login/', { data: { username: E2E_USER, password: E2E_PASSWORD } });
  if (!res.ok()) {
    res = await api.post('/api/auth/login/', { data: { email: E2E_USER, password: E2E_PASSWORD } });
  }
  if (!res.ok()) {
    throw new Error('Login failed: ' + res.status());
  }
  return api;
}

async function seed() {
  const api = await login();
  const created = {};

  async function post(path, data) {
    const res = await api.post(path, { data });
    if (!res.ok()) throw new Error('POST ' + path + ' failed: ' + res.status());
    return await res.json();
  }

  created.patient = await post('/api/patients/', { first_name: 'E2E', last_name: 'Patient', email: 'e2e.patient@example.com' });

  created.appointment = await post('/api/appointments/', {
    title: 'E2E Appointment',
    patient: created.patient?.id,
    start: new Date().toISOString(),
    end: new Date(Date.now() + 30 * 60 * 1000).toISOString(),
  });

  created.kpi = await post('/api/kpis/', { name: 'E2E KPI', value: 1 });

  created.operation = await post('/api/operations/', { name: 'E2E Operation', status: 'scheduled' });

  await api.dispose();
  console.log(JSON.stringify({ status: 'ok', created }, null, 2));
}

seed().catch((err) => {
  console.error(JSON.stringify({ status: 'error', message: err.message }, null, 2));
  process.exit(1);
});