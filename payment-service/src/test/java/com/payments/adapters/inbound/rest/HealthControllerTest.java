package com.payments.adapters.inbound.rest;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import com.payments.infrastructure.PaymentServiceApplication;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for {@link HealthController}.
 *
 * <p>The Spring Boot application context is started on a random port. The health
 * endpoint is public in the production security configuration, so no token is needed.
 */
@SpringBootTest(classes = PaymentServiceApplication.class, webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class HealthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    // -------------------------------------------------------------------------
    // Tests
    // -------------------------------------------------------------------------

    /**
     * Verifies that {@code GET /api/health} returns HTTP 200 with a JSON body
     * containing {@code "status": "ok"} and {@code "service": "payment-service"}.
     */
    @Test
    @DisplayName("GET /api/health returns 200 with status ok")
    void health_returnsOk() throws Exception {
        mockMvc.perform(get("/api/health")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(content().contentTypeCompatibleWith(MediaType.APPLICATION_JSON))
                .andExpect(jsonPath("$.status").value("ok"))
                .andExpect(jsonPath("$.service").value("payment-service"))
                .andExpect(jsonPath("$.timestamp").isNotEmpty());
    }
}
