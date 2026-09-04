package com.payments.adapters.outbound.persistence;

import com.payments.domain.model.Payment;
import com.payments.domain.model.PaymentMethod;
import com.payments.domain.model.PaymentStatus;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Persistence entity used by the in-memory repository adapter.
 *
 * <p>This is a plain POJO with no JPA or framework annotations. It mirrors the
 * fields of the {@link Payment} domain model and provides static factory methods
 * for converting between the two representations, keeping the domain model free
 * of persistence concerns.
 */
public class PaymentEntity {

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

    /** No-arg constructor required for frameworks and serialisation. */
    public PaymentEntity() {}

    /**
     * All-args constructor.
     *
     * @param id                   unique payment identifier
     * @param userId               owning user identifier
     * @param amount               monetary amount
     * @param currency             ISO 4217 currency code
     * @param status               current lifecycle status
     * @param method               payment gateway method
     * @param gatewayTransactionId gateway-assigned transaction id
     * @param description          human-readable description
     * @param createdAt            creation timestamp
     * @param updatedAt            last-update timestamp
     */
    public PaymentEntity(
            String id,
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

    // ---------------------------------------------------------------------------
    // Factory methods
    // ---------------------------------------------------------------------------

    /**
     * Creates a {@link PaymentEntity} from a {@link Payment} domain object.
     *
     * @param payment the domain payment to convert; must not be {@code null}
     * @return a new {@link PaymentEntity} with the same field values
     */
    public static PaymentEntity fromDomain(Payment payment) {
        return new PaymentEntity(
                payment.getId(),
                payment.getUserId(),
                payment.getAmount(),
                payment.getCurrency(),
                payment.getStatus(),
                payment.getMethod(),
                payment.getGatewayTransactionId(),
                payment.getDescription(),
                payment.getCreatedAt(),
                payment.getUpdatedAt()
        );
    }

    /**
     * Converts this entity back to a {@link Payment} domain object.
     *
     * @return a new {@link Payment} populated from this entity's fields
     */
    public Payment toDomain() {
        return Payment.builder()
                .id(id)
                .userId(userId)
                .amount(amount)
                .currency(currency)
                .status(status)
                .method(method)
                .gatewayTransactionId(gatewayTransactionId)
                .description(description)
                .createdAt(createdAt)
                .updatedAt(updatedAt)
                .build();
    }

    // ---------------------------------------------------------------------------
    // Getters and setters
    // ---------------------------------------------------------------------------

    /** @return the unique payment identifier */
    public String getId() { return id; }

    /** @param id the unique payment identifier */
    public void setId(String id) { this.id = id; }

    /** @return the owning user identifier */
    public String getUserId() { return userId; }

    /** @param userId the owning user identifier */
    public void setUserId(String userId) { this.userId = userId; }

    /** @return the monetary amount */
    public BigDecimal getAmount() { return amount; }

    /** @param amount the monetary amount */
    public void setAmount(BigDecimal amount) { this.amount = amount; }

    /** @return the ISO 4217 currency code */
    public String getCurrency() { return currency; }

    /** @param currency the ISO 4217 currency code */
    public void setCurrency(String currency) { this.currency = currency; }

    /** @return the current lifecycle status */
    public PaymentStatus getStatus() { return status; }

    /** @param status the current lifecycle status */
    public void setStatus(PaymentStatus status) { this.status = status; }

    /** @return the payment gateway method */
    public PaymentMethod getMethod() { return method; }

    /** @param method the payment gateway method */
    public void setMethod(PaymentMethod method) { this.method = method; }

    /** @return the gateway-assigned transaction identifier */
    public String getGatewayTransactionId() { return gatewayTransactionId; }

    /** @param gatewayTransactionId the gateway-assigned transaction identifier */
    public void setGatewayTransactionId(String gatewayTransactionId) {
        this.gatewayTransactionId = gatewayTransactionId;
    }

    /** @return the human-readable description */
    public String getDescription() { return description; }

    /** @param description the human-readable description */
    public void setDescription(String description) { this.description = description; }

    /** @return the creation timestamp */
    public LocalDateTime getCreatedAt() { return createdAt; }

    /** @param createdAt the creation timestamp */
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }

    /** @return the last-update timestamp */
    public LocalDateTime getUpdatedAt() { return updatedAt; }

    /** @param updatedAt the last-update timestamp */
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
