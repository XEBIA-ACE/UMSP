package com.payments.domain.model;

/**
 * Enumerates the supported payment gateway methods.
 *
 * <ul>
 *   <li>{@link #STRIPE}  – Process the payment via the Stripe gateway.</li>
 *   <li>{@link #PAYPAL}  – Process the payment via the PayPal gateway.</li>
 * </ul>
 */
public enum PaymentMethod {

    /** Stripe payment gateway. */
    STRIPE,

    /** PayPal payment gateway. */
    PAYPAL
}
