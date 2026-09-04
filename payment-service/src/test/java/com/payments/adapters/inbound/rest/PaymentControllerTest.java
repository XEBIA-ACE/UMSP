package com.payments.adapters.inbound.rest;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.payments.application.dto.ProcessPaymentRequest;
import com.payments.application.dto.ProcessPaymentResponse;
import com.payments.application.dto.RefundRequest;
import com.payments.application.dto.RefundResponse;
import com.payments.domain.model.Payment;
import com.payments.domain.model.PaymentMethod;
import com.payments.domain.model.PaymentStatus;
import com.payments.domain.ports.inbound.GetPaymentUseCase;
import com.payments.domain.ports.inbound.ProcessPaymentUseCase;
import com.payments.domain.ports.inbound.RefundPaymentUseCase;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Primary;
import org.springframework.http.MediaType;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.test.web.servlet.MockMvc;

import java.math.BigDecimal;
import java.time.LocalDateTime;

import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for {@link PaymentController}.
 *
 * <p>The Spring Boot application context is started on a random port. The three
 * use-case ports are replaced with Mockito mocks via {@link MockBean}. Security is
 * overridden to permit all requests so that tests focus on controller behaviour.
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@AutoConfigureMockMvc
class PaymentControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @MockBean
    private ProcessPaymentUseCase processPaymentUseCase;

    @MockBean
    private GetPaymentUseCase getPaymentUseCase;

    @MockBean
    private RefundPaymentUseCase refundPaymentUseCase;

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
     * Verifies that {@code POST /api/payments} with a valid request body returns
     * HTTP 201 Created and the expected JSON response fields.
     */
    @Test
    @DisplayName("POST /api/payments with valid body returns 201 Created")
    void processPayment_validRequest_returns201() throws Exception {
        ProcessPaymentRequest request = new ProcessPaymentRequest(
                "user-123",
                new BigDecimal("49.99"),
                "USD",
                PaymentMethod.STRIPE,
                "Test payment"
        );

        ProcessPaymentResponse response = new ProcessPaymentResponse(
                "pay-abc",
                PaymentStatus.COMPLETED,
                "pi_test_123",
                "Payment processed successfully"
        );

        when(processPaymentUseCase.process(any(ProcessPaymentRequest.class)))
                .thenReturn(response);

        mockMvc.perform(post("/api/payments")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(request)))
                .andExpect(status().isCreated())
                .andExpect(jsonPath("$.paymentId").value("pay-abc"))
                .andExpect(jsonPath("$.status").value("COMPLETED"))
                .andExpect(jsonPath("$.gatewayTransactionId").value("pi_test_123"));
    }

    /**
     * Verifies that {@code GET /api/payments/{id}} for a non-existent payment id
     * returns HTTP 404 Not Found.
     */
    @Test
    @DisplayName("GET /api/payments/{id} for unknown id returns 404 Not Found")
    void getPayment_unknownId_returns404() throws Exception {
        when(getPaymentUseCase.getById("unknown-id"))
                .thenThrow(new RuntimeException("Payment not found: unknown-id"));

        mockMvc.perform(get("/api/payments/unknown-id")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isNotFound());
    }

    /**
     * Verifies that {@code GET /api/payments/{id}} for an existing payment id
     * returns HTTP 200 OK with the payment details.
     */
    @Test
    @DisplayName("GET /api/payments/{id} for existing id returns 200 OK")
    void getPayment_existingId_returns200() throws Exception {
        Payment payment = Payment.builder()
                .id("pay-xyz")
                .userId("user-123")
                .amount(new BigDecimal("99.00"))
                .currency("USD")
                .status(PaymentStatus.COMPLETED)
                .method(PaymentMethod.STRIPE)
                .gatewayTransactionId("pi_test_xyz")
                .description("Test")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(getPaymentUseCase.getById("pay-xyz")).thenReturn(payment);

        mockMvc.perform(get("/api/payments/pay-xyz")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.id").value("pay-xyz"))
                .andExpect(jsonPath("$.status").value("COMPLETED"));
    }

    /**
     * Verifies that {@code POST /api/payments/{id}/refund} returns HTTP 200 OK
     * with the refund response.
     */
    @Test
    @DisplayName("POST /api/payments/{id}/refund returns 200 OK")
    void refundPayment_validRequest_returns200() throws Exception {
        RefundRequest refundRequest = new RefundRequest("pay-xyz", "Customer request");
        RefundResponse refundResponse = new RefundResponse(
                "pay-xyz", PaymentStatus.REFUNDED, "Refund processed successfully");

        when(refundPaymentUseCase.refund(any(RefundRequest.class))).thenReturn(refundResponse);

        mockMvc.perform(post("/api/payments/pay-xyz/refund")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(objectMapper.writeValueAsString(refundRequest)))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.paymentId").value("pay-xyz"))
                .andExpect(jsonPath("$.status").value("REFUNDED"));
    }
}
