# User Management and Payment Service

A production-ready monorepo containing two microservices that together handle user lifecycle management and multi-gateway payment processing.

| Service | Stack | Port |
|---|---|---|
| `user-management` | Node.js 20 · Express 4 | 3000 |
| `payment-service` | Java 17 · Spring Boot 3.2 | 8080 |

Both services follow **Hexagonal Architecture (Ports & Adapters)** — the domain and application layers are completely free of framework dependencies and are wired together at the infrastructure boundary.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Inbound Adapters                         │
│              (HTTP Controllers / REST Controllers)              │
└────────────────────────────┬────────────────────────────────────┘
                             │  calls
┌────────────────────────────▼────────────────────────────────────┐
│                     Application Layer                           │
│                  (Use Cases / App Services)                     │
│          depends only on Port interfaces (no I/O)               │
└──────┬──────────────────────────────────────────────┬───────────┘
       │ domain model                                 │ outbound ports
┌──────▼──────────┐                    ┌──────────────▼────────────┐
│  Domain Layer   │                    │    Outbound Adapters      │
│ (Entities/Ports)│                    │ (DB · Email · Stripe · …) │
└─────────────────┘                    └───────────────────────────┘
```

---

## Services

### 1. User Management Service (`/user-management`)

**Responsibilities**
- User registration with email verification
- Login with JWT issuance (OAuth2-compatible)
- Password recovery via email reset link
- Account verification via token

**Key endpoints**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/health` | Liveness probe |
| `GET` | `/api/ready` | Readiness probe |
| `POST` | `/api/auth/register` | Register a new user |
| `POST` | `/api/auth/login` | Authenticate and receive JWT |
| `POST` | `/api/auth/recover-password` | Request password reset email |
| `GET` | `/api/auth/verify/:token` | Verify account via email token |
| `GET` | `/api/users/profile` | Get authenticated user profile (JWT required) |

**Quick start**

```bash
cd user-management
cp .env.example .env          # fill in your values
npm install
npm start                     # production
npm run dev                   # development (nodemon)
npm test                      # run test suite with coverage
```

**Docker**

```bash
docker build -t user-management-service .
docker run -p 3000:3000 --env-file .env user-management-service
```

---

### 2. Payment Service (`/payment-service`)

**Responsibilities**
- Process payments via Stripe and PayPal
- Retrieve payment records
- Issue refunds
- Send payment confirmation notifications

**Key endpoints**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/health` | None | Liveness probe |
| `GET` | `/api/ready` | None | Readiness probe |
| `POST` | `/api/payments` | JWT | Process a new payment |
| `GET` | `/api/payments/{id}` | JWT | Retrieve payment by ID |
| `POST` | `/api/payments/{id}/refund` | JWT | Refund a completed payment |

**Quick start**

```bash
cd payment-service
cp .env.example .env          # fill in your values
./mvnw spring-boot:run        # or: mvn spring-boot:run
./mvnw test                   # run test suite
```

**Docker**

```bash
docker build -t payment-service .
docker run -p 8080:8080 --env-file .env payment-service
```

---

## Environment Variables

### User Management Service

| Variable | Default | Description |
|---|---|---|
| `PORT` | `3000` | HTTP listen port |
| `NODE_ENV` | `development` | Runtime environment |
| `JWT_SECRET` | *(required)* | Secret for signing JWTs |
| `JWT_EXPIRES_IN` | `7d` | JWT expiry duration |
| `SMTP_HOST` | — | SMTP server hostname |
| `SMTP_PORT` | `587` | SMTP server port |
| `SMTP_USER` | — | SMTP username |
| `SMTP_PASS` | — | SMTP password |
| `EMAIL_FROM` | — | Sender address for emails |

### Payment Service

| Variable | Default | Description |
|---|---|---|
| `SERVER_PORT` | `8080` | HTTP listen port |
| `STRIPE_API_KEY` | *(required)* | Stripe secret key (`sk_test_…`) |
| `PAYPAL_CLIENT_ID` | *(required)* | PayPal application client ID |
| `PAYPAL_CLIENT_SECRET` | *(required)* | PayPal application secret |
| `PAYPAL_MODE` | `sandbox` | `sandbox` or `live` |
| `OAUTH2_ISSUER_URI` | — | JWT issuer URI for token validation |
| `NOTIFICATION_EMAIL_ENABLED` | `false` | Enable email notifications |

---

## Running Both Services Together

```bash
# Terminal 1 — User Management
cd user-management && npm install && npm start

# Terminal 2 — Payment Service
cd payment-service && mvn spring-boot:run
```

Or with Docker Compose (example):

```yaml
version: "3.9"
services:
  user-management:
    build: ./user-management
    ports: ["3000:3000"]
    env_file: ./user-management/.env

  payment-service:
    build: ./payment-service
    ports: ["8080:8080"]
    env_file: ./payment-service/.env