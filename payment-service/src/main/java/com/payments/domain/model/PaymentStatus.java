package com.payments.domain.model;

/**
 * Represents the lifecycle status of a {@link Payment}.
 *
 * <ul>
 *   <li>{@link #PENDING}    – Payment has been created but not yet submitted to a gateway.</li>
 *   <li>{@link #PROCESSING} – Payment has been submitted to the gateway and is awaiting a result.</li>
 *   <li>{@link #COMPLETED}  – Payment was successfully processed by the gateway.</li>
 *   <li>{@link #FAILED}     – Payment was rejected or encountered an error at the gateway.</li>
 *   <li>{@link #REFUNDED}   – A previously completed payment has been fully refunded.</li>
 * </ul>
 */
public enum PaymentStatus {

    /** Payment created, not yet sent to a payment gateway. */
    PENDING,

    /** Payment submitted to the gateway; awaiting confirmation. */
    PROCESSING,

    /** Payment successfully completed. */
    COMPLETED,

    /** Payment failed at the gateway level. */
    FAILED,

    /** Payment has been refunded. */
    REFUNDED
}
