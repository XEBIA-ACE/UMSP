package com.payments.application.dto;

import com.payments.domain.model.PaymentStatus;

/**
 * Outbound DTO returned after a refund attempt.
 *
 * @param paymentId the unique identifier of the payment that was refunded
 * @param status    the resulting {@link PaymentStatus} after the refund (typically
 *                  {@link PaymentStatus#REFUNDED})
 * @param message   a human-readable summary of the refund outcome
 */
public record RefundResponse(
        String paymentId,
        PaymentStatus status,
        String message
) {}
