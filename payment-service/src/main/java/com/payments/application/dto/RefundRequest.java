package com.payments.application.dto;

import jakarta.validation.constraints.NotBlank;

/**
 * Inbound DTO carrying the data required to initiate a refund.
 *
 * @param paymentId the unique identifier of the payment to refund; must not be blank
 * @param reason    a human-readable reason for the refund; must not be blank
 */
public record RefundRequest(

        @NotBlank(message = "paymentId must not be blank")
        String paymentId,

        @NotBlank(message = "reason must not be blank")
        String reason
) {}
