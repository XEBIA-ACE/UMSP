'use strict';

/**
 * @fileoverview HTTP server factory.
 * Imports the Express app and wraps it in a Node.js HTTP server.
 */

const http = require('http');
const { createApp } = require('./app');

/**
 * Creates an HTTP server backed by the configured Express application.
 *
 * @returns {http.Server} Node.js HTTP server (not yet listening).
 */
function createServer() {
  const app = createApp();
  return http.createServer(app);
}

module.exports = { createServer };
