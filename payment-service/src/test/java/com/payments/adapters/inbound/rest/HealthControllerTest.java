package com.payments.adapters.inbound.rest;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.test.web.servlet.MockMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for {@link HealthController}.
 *
 * <p>The Spring Boot application context is started on a random port. Security is
 * overridden via a {@link TestConfiguration} that permits all requests so that the
 * health endpoint can be reached without a JWT token.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class HealthControllerTest {

    @Autowired
    private MockMvc mockMvc;

    // -------------------------------------------------------------------------
    // Test-only security configuration – permits all requests
    // -------------------------------------------------------------------------

    /**
     * Overrides the production {@link SecurityFilterChain} for tests so that all
     * requests are permitted without authentication.
     */
    @TestConfiguration
    static class TestSecurityConfig {

        @Bean
        @Primary
        SecurityFilterChain testSecurityFilterChain(HttpSecurity http) throws Exception {
            http
                .csrf(csrf -> csrf.disable())
                .authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
            return http.build();
        }
    }

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
