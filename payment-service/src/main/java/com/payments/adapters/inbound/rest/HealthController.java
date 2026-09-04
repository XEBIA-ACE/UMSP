package com.payments.adapters.inbound.rest;

import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * REST adapter that exposes a simple liveness / readiness health-check endpoint.
 *
 * <p>This controller is intentionally kept free of business logic and is permitted
 * without authentication so that load balancers and orchestration platforms (e.g.
 * Kubernetes) can probe the service without credentials.
 *
 * <p>Base path: {@code /api/health}
 */
@RestController
@RequestMapping("/api/health")
public class HealthController {

    /**
     * Returns a lightweight health-check payload.
     *
     * <p>Example response body:
     * <pre>{@code
     * {
     *   "status"    : "ok",
     *   "service"   : "payment-service",
     *   "timestamp" : "2024-01-15T10:30:00Z"
     * }
     * }</pre>
     *
     * @return {@code 200 OK} with a JSON map containing {@code status}, {@code service},
     *         and {@code timestamp} fields
     */
    @GetMapping
    public ResponseEntity<Map<String, String>> health() {
        // TODO: Map.of() is available in Java 9+; retained as-is since Java 17 is still the target runtime.
        // Spring Boot 3.1 (vs 3.2) does not affect this controller's logic.
        Map<String, String> body = new HashMap<>();
        body.put("status", "ok");
        body.put("service", "payment-service");
        body.put("timestamp", Instant.now().toString());
        return ResponseEntity.ok(body);
    }
}