package com.payments.application.dto;

import com.payments.domain.model.PaymentMethod;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.math.BigDecimal;

/**
 * Inbound DTO carrying all data required to initiate a new payment.
 *
 * <p>Bean Validation annotations are applied so that the REST layer can
 * reject malformed requests before they reach the application service.
 *
 * @param userId      the identifier of the user initiating the payment; must not be blank
 * @param amount      the monetary amount to charge; must be a positive value
 * @param currency    the ISO 4217 currency code (e.g. "USD"); must not be blank
 * @param method      the payment gateway to use ({@link PaymentMethod#STRIPE} or
 *                    {@link PaymentMethod#PAYPAL}); must not be {@code null}
 * @param description a human-readable description of the payment purpose; must not be blank
 */
public record ProcessPaymentRequest(

        @NotBlank(message = "userId must not be blank")
        String userId,

        @NotNull(message = "amount must not be null")
        @Positive(message = "amount must be positive")
        BigDecimal amount,

        @NotBlank(message = "currency must not be blank")
        String currency,

        @NotNull(message = "method must not be null")
        PaymentMethod method,

        @NotBlank(message = "description must not be blank")
        String description
) {}
