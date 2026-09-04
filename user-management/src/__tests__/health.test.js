'use strict';

/**
 * @fileoverview Integration tests for the health endpoint.
 * Verifies that GET /api/health returns 200 with the expected payload.
 */

const request = require('supertest');
const { createApp } = require('../infrastructure/app');

describe('GET /api/health', () => {
  let app;

  beforeAll(() => {
    app = createApp();
  });

  it('should return 200 with status "ok"', async () => {
    const res = await request(app).get('/api/health');

    expect(res.status).toBe(200);
    expect(res.body).toMatchObject({
      status: 'ok',
      service: 'user-management',
    });
  });

  it('should include a valid ISO timestamp', async () => {
    const res = await request(app).get('/api/health');

    expect(res.body.timestamp).toBeDefined();
    expect(() => new Date(res.body.timestamp)).not.toThrow();
    expect(new Date(res.body.timestamp).toISOString()).toBe(res.body.timestamp);
  });

  it('should return Content-Type application/json', async () => {
    const res = await request(app).get('/api/health');

    expect(res.headers['content-type']).toMatch(/application\/json/);
  });
});
