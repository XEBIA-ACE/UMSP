# ============================================================
# Multi-stage Dockerfile for Payment Service
# ============================================================
# Stage 1 – Build the fat JAR with Maven
# Stage 2 – Run the JAR on a minimal JRE image
# ============================================================

# ------------------------------------
# Stage 1: Build
# ------------------------------------
FROM maven:3.9-eclipse-temurin-17-alpine AS builder

WORKDIR /build

# Copy the POM first so that Maven can download dependencies
# before the source code is copied (layer-cache optimisation).
COPY pom.xml .
RUN mvn dependency:go-offline --no-transfer-progress

# Copy the full source tree and build the fat JAR
COPY src ./src
RUN mvn package -DskipTests --no-transfer-progress

# ------------------------------------
# Stage 2: Runtime
# ------------------------------------
FROM eclipse-temurin:17-jre-alpine AS runtime

WORKDIR /app

# Copy only the fat JAR produced by the builder stage
COPY --from=builder /build/target/payment-service-*.jar payment-service.jar

# Expose the default application port
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "payment-service.jar"]
