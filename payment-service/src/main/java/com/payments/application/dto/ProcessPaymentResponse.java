package com.payments.application.dto;

import com.payments.domain.model.PaymentStatus;

/**
 * Outbound DTO returned after a payment processing attempt.
 *
 * @param paymentId            the unique identifier assigned to the created payment
 * @param status               the resulting {@link PaymentStatus} after processing
 * @param gatewayTransactionId the transaction identifier returned by the payment gateway;
 *                             may be {@code null} if the gateway call failed
 * @param message              a human-readable summary of the outcome
 */
public record ProcessPaymentResponse(
        String paymentId,
        PaymentStatus status,
        String gatewayTransactionId,
        String message
) {}
