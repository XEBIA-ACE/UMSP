package com.payments.domain.ports.outbound;

import java.math.BigDecimal;

/**
 * Outbound port (secondary port) for charging payments via the PayPal gateway.
 *
 * <p>Implementations of this interface are infrastructure adapters and live in
 * the adapters layer. This interface belongs to the domain layer and must not
 * depend on any framework or infrastructure concern.
 */
public interface PayPalGatewayPort {

    /**
     * Submits a charge request to the PayPal payment gateway.
     *
     * @param userId      the identifier of the user being charged
     * @param amount      the monetary amount to charge
     * @param currency    the ISO 4217 currency code (e.g. "USD")
     * @param description a human-readable description of the charge
     * @return a {@link ChargeResult} describing the outcome of the charge attempt
     */
    ChargeResult charge(String userId, BigDecimal amount, String currency, String description);

    /**
     * Encapsulates the result of a PayPal charge attempt.
     *
     * @param transactionId the PayPal-assigned transaction / order id;
     *                      may be {@code null} on failure
     * @param success       {@code true} if the charge was accepted by PayPal
     * @param errorMessage  human-readable error detail; {@code null} on success
     */
    record ChargeResult(String transactionId, boolean success, String errorMessage) {}
}
