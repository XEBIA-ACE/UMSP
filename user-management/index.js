'use strict';

require('dotenv').config();

const { createServer } = require('./src/infrastructure/server');
const env = require('./src/infrastructure/config/env');

const server = createServer();

server.listen(env.PORT, () => {
  console.log(
    `[user-management] Server running on port ${env.PORT} (${env.NODE_ENV})`
  );
});

// Graceful shutdown
const shutdown = (signal) => {
  console.log(`[user-management] Received ${signal}. Shutting down gracefully…`);
  server.close(() => {
    console.log('[user-management] HTTP server closed.');
    process.exit(0);
  });
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
