package com.payments.domain.ports.outbound;

import com.payments.domain.model.Payment;

import java.util.List;
import java.util.Optional;

/**
 * Outbound port (secondary port) for persisting and retrieving {@link Payment} entities.
 *
 * <p>Implementations of this interface are infrastructure adapters (e.g. in-memory map,
 * relational database, NoSQL store) and live in the adapters layer.
 *
 * <p>This interface belongs to the domain layer and must not depend on any
 * framework or infrastructure concern.
 */
public interface PaymentRepositoryPort {

    /**
     * Persists a new {@link Payment} to the underlying store.
     *
     * @param payment the payment to save; must not be {@code null}
     * @return the saved payment (may include generated fields)
     */
    Payment save(Payment payment);

    /**
     * Retrieves a {@link Payment} by its unique identifier.
     *
     * @param id the unique payment identifier; must not be {@code null}
     * @return an {@link Optional} containing the payment if found, or empty
     */
    Optional<Payment> findById(String id);

    /**
     * Retrieves all payments belonging to a specific user.
     *
     * @param userId the user identifier; must not be {@code null}
     * @return a (possibly empty) list of payments for the given user
     */
    List<Payment> findByUserId(String userId);

    /**
     * Updates an existing {@link Payment} in the underlying store.
     *
     * @param payment the payment with updated fields; must not be {@code null}
     * @return the updated payment
     */
    Payment update(Payment payment);
}
