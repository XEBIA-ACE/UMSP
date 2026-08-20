package com.payments.adapters.outbound.stripe;

import com.payments.domain.ports.outbound.StripeGatewayPort;
import com.stripe.Stripe;
import com.stripe.exception.StripeException;
import com.stripe.model.PaymentIntent;
import com.stripe.param.PaymentIntentCreateParams;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;

/**
 * Outbound adapter that delegates payment charges to the Stripe payment gateway.
 *
 * <p>This adapter implements {@link StripeGatewayPort} and uses the official
 * {@code stripe-java} SDK to create a {@link PaymentIntent}. The Stripe API key
 * is injected from application configuration.
 *
 * <p>Amounts are converted from a decimal representation (e.g. {@code 9.99}) to
 * the smallest currency unit expected by Stripe (e.g. {@code 999} cents for USD).
 */
@Component
public class StripeGatewayAdapter implements StripeGatewayPort {

    private final String apiKey;

    /**
     * Constructs the adapter with the Stripe API key.
     *
     * @param apiKey the Stripe secret API key, injected from {@code stripe.api.key}
     */
    public StripeGatewayAdapter(@Value("${stripe.api.key}") String apiKey) {
        this.apiKey = apiKey;
    }

    /**
     * {@inheritDoc}
     *
     * <p>Creates a Stripe {@link PaymentIntent} with {@code automatic_payment_methods}
     * enabled. The amount is converted to the smallest currency unit (e.g. cents).
     *
     * @return a {@link ChargeResult} with the PaymentIntent id on success, or an error
     *         message on failure
     */
    @Override
    public ChargeResult charge(
            String userId,
            BigDecimal amount,
            String currency,
            String description) {

        // Set the API key for this request
        Stripe.apiKey = apiKey;

        try {
            // Convert decimal amount to smallest currency unit (e.g. dollars → cents)
            long amountInSmallestUnit = amount
                    .multiply(BigDecimal.valueOf(100))
                    .longValue();

            PaymentIntentCreateParams params = PaymentIntentCreateParams.builder()
                    .setAmount(amountInSmallestUnit)
                    .setCurrency(currency.toLowerCase())
                    .setDescription(description)
                    .putMetadata("userId", userId)
                    .setAutomaticPaymentMethods(
                            PaymentIntentCreateParams.AutomaticPaymentMethods.builder()
                                    .setEnabled(true)
                                    .build()
                    )
                    .build();

            PaymentIntent intent = PaymentIntent.create(params);
            return new ChargeResult(intent.getId(), true, null);

        } catch (StripeException e) {
            return new ChargeResult(null, false, e.getMessage());
        }
    }
}
