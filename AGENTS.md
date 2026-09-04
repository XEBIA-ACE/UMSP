# AGENTS.md — User Management and Payment Service

## 1. Stack

| Technology | Role |
|---|---|
| **Node.js 20 LTS** | Runtime for Express API gateway / BFF layer |
| **Express 4.x** | HTTP routing, middleware, request validation |
| **Java 21 (LTS)** | Runtime for Spring Boot core business services |
| **Spring Boot 3.x** | User management, payment orchestration microservices |
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
│   │   │   │   │   ├── UserRepository.java
│   │   │   │   │   └── VerificationTokenRepository.java
│   │   │   │   ├── model/
│   │   │   │   │   ├── User.java                  # JPA entity
│   │   │   │   │   ├── VerificationToken.java
│   │   │   │   │   └── enums/
│   │   │   │   │       ├── UserStatus.java
│   │   │   │   │       └── UserRole.java
│   │   │   │   ├── dto/
│   │   │   │   │   ├── request/
│   │   │   │   │   │   ├── RegisterRequest.java
│   │   │   │   │   │   ├── LoginRequest.java
│   │   │   │   │   │   └── PasswordResetRequest.java
│   │   │   │   │   └── response/
│   │   │   │   │       ├── AuthResponse.java
│   │   │   │   │       └── UserResponse.java
│   │   │   │   ├── exception/
│   │   │   │   │   ├── GlobalExceptionHandler.java  # @RestControllerAdvice
│   │   │   │   │   ├── UserAlreadyExistsException.java
│   │   │   │   │   └── InvalidTokenException.java
│   │   │   │   └── security/
│   │   │   │       ├── JwtAuthFilter.java
│   │   │   │       └── UserDetailsServiceImpl.java
│   │   │   └── resources/
│   │   │       ├── application.yml
│   │   │       ├── application-dev.yml
│   │   │       ├── application-prod.yml
│   │   │       └── db/migration/                  # Flyway scripts
│   │   │           ├── V1__create_users_table.sql
│   │   │           └── V2__create_verification_tokens_table.sql
│   │   └── test/
│   │       └── java/com/company/userservice/
│   │           ├── controller/
│   │           ├── service/
│   │           └── repository/
│
└── payment-service/                   # Spring Boot — Payment Orchestration
    ├── Dockerfile
    ├── pom.xml
    ├── src/
    │   ├── main/
    │   │   ├── java/com/company/paymentservice/
    │   │   │   ├── PaymentServiceApplication.java
    │   │   │   ├── config/
    │   │   │   │   ├── SecurityConfig.java
    │   │   │   │   ├── StripeConfig.java           # Stripe SDK initialisation
    │   │   │   │   └── PayPalConfig.java           # PayPal SDK initialisation
    │   │   │   ├── controller/
    │   │   │   │   ├── PaymentController.java      # /internal/payments/*
    │   │   │   │   └── WebhookController.java      # /internal/webhooks/*
    │   │   │   ├── service/
    │   │   │   │   ├── PaymentOrchestrationService.java
    │   │   │   │   ├── StripePaymentService.java
    │   │   │   │   ├── PayPalPaymentService.java
    │   │   │   │   └── IdempotencyService.java     # Redis-backed idempotency
    │   │   │   ├── gateway/
    │   │   │   │   ├── PaymentGateway.java         # Interface
    │   │   │   │   ├── StripeGateway.java
    │   │   │   │   └── PayPalGateway.java
    │   │   │   ├── repository/
    │   │   │   │   ├── PaymentRepository.java
    │   │   │   │   └── RefundRepository.java
    │   │   │   ├── model/
    │   │   │   │   ├── Payment.java
    │   │   │   │   ├── Refund.java
    │   │   │   │   └── enums/
    │   │   │   │       ├── PaymentStatus.java
    │   │   │   │       └── GatewayProvider.java
    │   │   │   ├── dto/
    │   │   │   │   ├── request/
    │   │   │   │   │   └── PaymentRequest.java
    │   │   │   │   └── response/
    │   │   │   │       └── PaymentResponse.java
    │   │   │   └── exception/
    │   │   │       ├── GlobalExceptionHandler.java
    │   │   │       ├── PaymentFailedException.java
    │   │   │       └── GatewayUnavailableException.java
    │   │   └── resources/
    │   │       ├── application.yml
    │   │       ├── application-dev.yml
    │   │       ├── application-prod.yml
    │   │       └── db/migration/
    │   │           ├── V1__create_payments_table.sql
    │   │           └── V2__create_refunds_table.sql
    │   └── test/
    │       └── java/com/company/paymentservice/
    │           ├── controller/
    │           ├── service/
    │           └── gateway/
```

---

## 3. Required Workflow

The agent **must** follow these steps in order. Do not skip or reorder steps.

### Step 1 — Read and Understand Specifications
- Read all story-level spec documents provided in the task context.
- Identify every functional requirement, edge case, and constraint.
- Note all external dependencies (Stripe, PayPal, OAuth2 provider, SMTP/SendGrid).

### Step 2 — Create `tasks.md`
- Before writing any code, create `tasks.md` at the repository root.
- Structure it as a checklist with sections: **Setup**, **Gateway (Node.js)**, **User Service (Java)**, **Payment Service (Java)**, **Testing**, **Docker/CI**, **Security Hardening**.
- Each task must be atomic, testable, and map to a single file or function.
- Mark tasks `[ ]` (pending), `[x]` (done), or `[~]` (in progress).

### Step 3 — Environment and Scaffold Setup
- Copy `.env.example` to `.env` (never commit `.env`).
- Run `docker-compose up -d postgres redis` before any service starts.
- Install Node.js dependencies: `cd gateway && npm ci`.
- Build Java services: `cd user-service && ./mvnw clean install -DskipTests`.
- Confirm all containers are healthy before proceeding.

### Step 4 — Implement in Dependency Order
Implement in this exact order to respect inter-service dependencies:

1. Database migrations (Flyway scripts for both Java services)
2. JPA models and repositories (`user-service` → `payment-service`)
3. DTOs and exception classes
4. Service layer (business logic, no HTTP concerns)
5. Security configuration (JWT filter, OAuth2 resource server)
6. Controllers (internal REST endpoints)
7. Node.js gateway routes, middleware, and proxy services
8. Email service integration (SendGrid/JavaMail)
9. Stripe and PayPal gateway implementations
10. Webhook handlers with signature verification

### Step 5 — Write Tests Alongside Each Component
- Write tests **immediately** after implementing each component — not at the end.
- Every service method must have a corresponding unit test before moving to the next component.
- Run the relevant test suite after each component is complete.

### Step 6 — Integration Validation
- Start all services via `docker-compose up`.
- Execute the full integration test suite: `npm test` (gateway) and `./mvnw verify` (each Java service).
- All tests must pass with zero failures before proceeding.

### Step 7 — Coverage and Quality Gates
- Generate coverage reports: `npm run test:coverage` and `./mvnw verify -Pjacoco`.
- Confirm ≥ 90% line and branch coverage in all three services.
- Run `npm run lint` and `./mvnw checkstyle:check` — zero violations permitted.

### Step 8 — Security Hardening Checklist
Before marking any task complete, verify:
- [ ] No secrets in source code or committed `.env` files
- [ ] All payment webhook endpoints verify provider signatures
- [ ] Passwords hashed with BCrypt (cost factor ≥ 12)
- [ ] All endpoints behind authentication except `/auth/register`, `/auth/login`, `/auth/verify`, `/auth/forgot-password`
- [ ] PCI-DSS: raw card data never logged or stored; only tokenised references stored
- [ ] Rate limiting applied to all auth endpoints

### Step 9 — Update `tasks.md`
- Mark all completed tasks `[x]`.
- Add any discovered sub-tasks that were not in the original list.
- Leave a **Summary** section at the bottom describing what was built and any deviations from spec.

---

## 4. Coding Conventions

### General
- All code must be production-ready — no `TODO`, `FIXME`, or placeholder comments in committed code.
- Correlation IDs must be propagated across all service boundaries via `X-Correlation-ID` HTTP header.
- All structured logs must be JSON format; never log sensitive data (passwords, tokens, card numbers).

### Node.js / Express (Gateway)
- **File naming:** `camelCase` for files (`authController.js`), `PascalCase` for classes.
- **Module pattern:** Use ES modules (`import`/`export`) with `"type": "module"` in `package.json`.
- **Config:** All configuration sourced from `src/config/index.js` — never