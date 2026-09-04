# AGENTS.md — User Management and Payment Service

## 1. Stack

| Technology | Role |
|---|---|
| **Node.js 20 LTS** | Runtime for Express API gateway / BFF layer |
| **Express 4.x** | HTTP routing, middleware, request validation |
| **Java 11 (LTS)** | Runtime for Spring Boot core business services |
| **Spring Boot 2.x** | User management, payment orchestration microservices |
| **Spring Security + OAuth2** | Authentication, authorization, token management |
| **Spring Data JPA / Hibernate** | ORM for user and transaction persistence |
| **Stripe Java SDK** | Stripe payment gateway integration |
| **PayPal REST SDK (Java)** | PayPal payment gateway integration |
| **PostgreSQL 15** | Primary relational database |
| **Redis 7** | Session store, token cache, idempotency keys |
| **JavaMail / SendGrid** | Transactional email (verification, recovery) |
| **Flyway** | Database schema migrations (Java service) |
| **Jest + Supertest** | Unit and integration tests for Node.js layer |
| **JUnit 5 + Mockito** | Unit and integration tests for Spring Boot services |
| **Testcontainers** | Containerised DB/Redis for Java integration tests |
| **Docker + Docker Compose** | Local development and CI environment |
| **GitHub Actions** | CI/CD pipeline |

---

## 2. Project Structure

```
user-payment-service/
├── AGENTS.md                          # This file
├── tasks.md                           # Agent-generated task tracker (created before coding)
├── docker-compose.yml                 # Orchestrates all services locally
├── docker-compose.test.yml            # Isolated test environment
├── .env.example                       # All required env vars documented (no secrets)
├── .github/
│   └── workflows/
│       ├── ci.yml                     # Main CI pipeline
│       └── security-scan.yml          # SAST / dependency audit
│
├── gateway/                           # Node.js / Express API Gateway
│   ├── Dockerfile
│   ├── package.json
│   ├── package-lock.json
│   ├── jest.config.js
│   ├── .eslintrc.js
│   ├── .prettierrc
│   ├── src/
│   │   ├── app.js                     # Express app factory (no listen() here)
│   │   ├── server.js                  # Entry point — calls app.listen()
│   │   ├── config/
│   │   │   ├── index.js               # Centralised config from env vars
│   │   │   └── oauth2.js              # OAuth2 client configuration
│   │   ├── middleware/
│   │   │   ├── authenticate.js        # JWT / OAuth2 token verification
│   │   │   ├── rateLimiter.js         # express-rate-limit setup
│   │   │   ├── requestLogger.js       # Morgan + correlation ID injection
│   │   │   ├── errorHandler.js        # Global error handler
│   │   │   └── validateSchema.js      # Joi/Zod request validation wrapper
│   │   ├── routes/
│   │   │   ├── index.js               # Mounts all routers
│   │   │   ├── auth.routes.js         # /auth/* — login, register, refresh
│   │   │   ├── user.routes.js         # /users/* — profile, verification
│   │   │   └── payment.routes.js      # /payments/* — initiate, confirm, webhook
│   │   ├── controllers/
│   │   │   ├── auth.controller.js
│   │   │   ├── user.controller.js
│   │   │   └── payment.controller.js
│   │   ├── services/
│   │   │   ├── authService.js         # Proxies to Spring Auth service
│   │   │   ├── userService.js         # Proxies to Spring User service
│   │   │   └── paymentService.js      # Proxies to Spring Payment service
│   │   ├── schemas/
│   │   │   ├── auth.schema.js         # Zod schemas for auth endpoints
│   │   │   ├── user.schema.js
│   │   │   └── payment.schema.js
│   │   └── utils/
│   │       ├── httpClient.js          # Axios instance with retry + circuit breaker
│   │       ├── logger.js              # Winston structured JSON logger
│   │       └── correlationId.js       # UUID correlation ID helpers
│   └── tests/
│       ├── unit/
│       │   ├── middleware/
│       │   └── controllers/
│       └── integration/
│           ├── auth.test.js
│           ├── user.test.js
│           └── payment.test.js
│
├── user-service/                      # Spring Boot — User Management
│   ├── Dockerfile
│   ├── pom.xml
│   ├── src/
│   │   ├── main/
│   │   │   ├── java/com/company/userservice/
│   │   │   │   ├── UserServiceApplication.java
│   │   │   │   ├── config/
│   │   │   │   │   ├── SecurityConfig.java        # Spring Security + OAuth2 resource server
│   │   │   │   │   ├── OAuth2Config.java
│   │   │   │   │   └── MailConfig.java
│   │   │   │   ├── controller/
│   │   │   │   │   ├── AuthController.java        # /internal/auth/*
│   │   │   │   │   └── UserController.java        # /internal/users/*
│   │   │   │   ├── service/
│   │   │   │   │   ├── AuthService.java
│   │   │   │   │   ├── UserService.java
│   │   │   │   │   ├── EmailService.java          # Verification + recovery emails
│   │   │   │   │   └── TokenService.java          # JWT generation/validation
│   │   │   │   ├── repository/
│   │   │   │   │   ├── UserReposit