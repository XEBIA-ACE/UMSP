package com.payments.domain.model;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Objects;

/**
 * Core domain entity representing a payment transaction.
 *
 * <p>This is a plain Java object with no framework dependencies, keeping the domain
 * layer independent of infrastructure concerns (hexagonal architecture).
 *
 * <p>Instances are created via the nested {@link Builder} class or via
 * {@link #toBuilder()} to produce a modified copy.
 *
 * <pre>{@code
 * Payment payment = Payment.builder()
 *     .id("pay_123")
 *     .userId("user_456")
 *     .amount(new BigDecimal("49.99"))
 *     .currency("USD")
 *     .status(PaymentStatus.PENDING)
 *     .method(PaymentMethod.STRIPE)
 *     .description("Order #789")
 *     .createdAt(LocalDateTime.now())
 *     .updatedAt(LocalDateTime.now())
 *     .build();
 * }</pre>
 */
public class Payment {

    /** Unique identifier for this payment (e.g. UUID). */
    private final String id;

    /** Identifier of the user who initiated the payment. */
    private final String userId;

    /** Monetary amount to be charged. */
    private final BigDecimal amount;

    /** ISO 4217 currency code (e.g. "USD", "EUR"). */
    private final String currency;

    /** Current lifecycle status of the payment. */
    private final PaymentStatus status;

    /** Gateway used to process this payment. */
    private final PaymentMethod method;

    /** Transaction identifier returned by the payment gateway, may be {@code null} before processing. */
    private final String gatewayTransactionId;

    /** Human-readable description of the payment purpose. */
    private final String description;

    /** Timestamp when this payment record was first created. */
    private final LocalDateTime createdAt;

    /** Timestamp of the most recent update to this payment record. */
    private final LocalDateTime updatedAt;

    /**
     * No-arg constructor required for certain serialisation frameworks.
     * Prefer using {@link Builder} for normal construction.
     */
    public Payment() {
        this.id = null;
        this.userId = null;
        this.amount = null;
        this.currency = null;
        this.status = null;
        this.method = null;
        this.gatewayTransactionId = null;
        this.description = null;
        this.createdAt = null;
        this.updatedAt = null;
    }

    /**
     * All-args constructor. Prefer using {@link Builder} for readability.
     *
     * @param id                   unique payment identifier
     * @param userId               owning user identifier
     * @param amount               monetary amount
     * @param currency             ISO 4217 currency code
     * @param status               current payment status
     * @param method               payment gateway method
     * @param gatewayTransactionId gateway-assigned transaction id
     * @param description          human-readable description
     * @param createdAt            creation timestamp
     * @param updatedAt            last-updated timestamp
     */
    public Payment(String id,
                   String userId,
                   BigDecimal amount,
                   String currency,
                   PaymentStatus status,
                   PaymentMethod method,
                   String gatewayTransactionId,
                   String description,
                   LocalDateTime createdAt,
                   LocalDateTime updatedAt) {
        this.id = id;
        this.userId = userId;
        this.amount = amount;
        this.currency = currency;
        this.status = status;
        this.method = method;
        this.gatewayTransactionId = gatewayTransactionId;
        this.description = description;
        this.createdAt = createdAt;
        this.updatedAt = updatedAt;
    }

    // -------------------------------------------------------------------------
    // Accessors
    // -------------------------------------------------------------------------

    /** @return unique payment identifier */
    public String getId() { return id; }

    /** @return owning user identifier */
    public String getUserId() { return userId; }

    /** @return monetary amount */
    public BigDecimal getAmount() { return amount; }

    /** @return ISO 4217 currency code */
    public String getCurrency() { return currency; }

    /** @return current payment status */
    public PaymentStatus getStatus() { return status; }

    /** @return payment gateway method */
    public PaymentMethod getMethod() { return method; }

    /** @return gateway-assigned transaction id, or {@code null} if not yet processed */
    public String getGatewayTransactionId() { return gatewayTransactionId; }

    /** @return human-readable description */
    public String getDescription() { return description; }

    /** @return creation timestamp */
    public LocalDateTime getCreatedAt() { return createdAt; }

    /** @return last-updated timestamp */
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    // -------------------------------------------------------------------------
    // Builder
    // -------------------------------------------------------------------------

    /**
     * Returns a new {@link Builder} for constructing a {@link Payment}.
     *
     * @return a fresh builder instance
     */
    public static Builder builder() {
        return new Builder();
    }

    /**
     * Returns a {@link Builder} pre-populated with this instance's values,
     * allowing a modified copy to be produced without altering the original.
     *
     * @return a builder seeded with this payment's field values
     */
    public Builder toBuilder() {
        return new Builder()
                .id(this.id)
                .userId(this.userId)
                .amount(this.amount)
                .currency(this.currency)
                .status(this.status)
                .method(this.method)
                .gatewayTransactionId(this.gatewayTransactionId)
                .description(this.description)
                .createdAt(this.createdAt)
                .updatedAt(this.updatedAt);
    }

    /**
     * Fluent builder for {@link Payment}.
     */
    public static final class Builder {

        private String id;
        private String userId;
        private BigDecimal amount;
        private String currency;
        private PaymentStatus status;
        private PaymentMethod method;
        private String gatewayTransactionId;
        private String description;
        private LocalDateTime createdAt;
        private LocalDateTime updatedAt;

        private Builder() {}

        public Builder id(String id) { this.id = id; return this; }
        public Builder userId(String userId) { this.userId = userId; return this; }
        public Builder amount(BigDecimal amount) { this.amount = amount; return this; }
        public Builder currency(String currency) { this.currency = currency; return this; }
        public Builder status(PaymentStatus status) { this.status = status; return this; }
        public Builder method(PaymentMethod method) { this.method = method; return this; }
        public Builder gatewayTransactionId(String gatewayTransactionId) { this.gatewayTransactionId = gatewayTransactionId; return this; }
        public Builder description(String description) { this.description = description; return this; }
        public Builder createdAt(LocalDateTime createdAt) { this.createdAt = createdAt; return this; }
        public Builder updatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; return this; }

        /**
         * Constructs the {@link Payment} from the current builder state.
         *
         * @return a new {@link Payment} instance
         */
        public Payment build() {
            return new Payment(id, userId, amount, currency, status, method,
                    gatewayTransactionId, description, createdAt, updatedAt);
        }
    }

    // -------------------------------------------------------------------------
    // Object overrides
    // -------------------------------------------------------------------------

    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        Payment payment = (Payment) o;
        return Objects.equals(id, payment.id);
    }

    @Override
    public int hashCode() {
        return Objects.hash(id);
    }

    @Override
    public String toString() {
        return "Payment{" +
                "id='" + id + '\'' +
                ", userId='" + userId + '\'' +
                ", amount=" + amount +
                ", currency='" + currency + '\'' +
                ", status=" + status +
                ", method=" + method +
                ", gatewayTransactionId='" + gatewayTransactionId + '\'' +
                ", description='" + description + '\'' +
                ", createdAt=" + createdAt +
                ", updatedAt=" + updatedAt +
                '}';
    }
}