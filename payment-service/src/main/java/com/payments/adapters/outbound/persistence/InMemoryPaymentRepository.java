package com.payments.adapters.outbound.persistence;

import com.payments.domain.model.Payment;
import com.payments.domain.ports.outbound.PaymentRepositoryPort;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.stream.Collectors;

/**
 * In-memory implementation of {@link PaymentRepositoryPort} backed by a
 * {@link ConcurrentHashMap}.
 *
 * <p>This adapter is suitable for development, testing, and demo purposes.
 * Replace it with a database-backed adapter (e.g. JPA, R2DBC) for production use.
 *
 * <p>All operations are thread-safe due to the use of {@link ConcurrentHashMap}.
 */
@Repository
public class InMemoryPaymentRepository implements PaymentRepositoryPort {

    private final ConcurrentHashMap<String, PaymentEntity> store = new ConcurrentHashMap<>();

    /**
     * {@inheritDoc}
     *
     * <p>Converts the domain {@link Payment} to a {@link PaymentEntity} and stores it
     * under the payment's id.
     *
     * @throws IllegalArgumentException if a payment with the same id already exists
     */
    @Override
    public Payment save(Payment payment) {
        PaymentEntity entity = PaymentEntity.fromDomain(payment);
        store.put(entity.getId(), entity);
        return entity.toDomain();
    }

    /**
     * {@inheritDoc}
     *
     * @return an {@link Optional} containing the payment if found, or empty
     */
    @Override
    public Optional<Payment> findById(String id) {
        PaymentEntity entity = store.get(id);
        return Optional.ofNullable(entity).map(PaymentEntity::toDomain);
    }

    /**
     * {@inheritDoc}
     *
     * <p>Performs a linear scan of all stored entities and filters by {@code userId}.
     *
     * @return a (possibly empty) list of payments belonging to the given user
     */
    @Override
    public List<Payment> findByUserId(String userId) {
        return store.values().stream()
                .filter(entity -> userId.equals(entity.getUserId()))
                .map(PaymentEntity::toDomain)
                .collect(Collectors.toList());
    }

    /**
     * {@inheritDoc}
     *
     * <p>Replaces the stored entity for the payment's id with the updated version.
     *
     * @throws RuntimeException if no payment with the given id exists in the store
     */
    @Override
    public Payment update(Payment payment) {
        if (!store.containsKey(payment.getId())) {
            throw new RuntimeException("Cannot update non-existent payment: " + payment.getId());
        }
        PaymentEntity entity = PaymentEntity.fromDomain(payment);
        store.put(entity.getId(), entity);
        return entity.toDomain();
    }
}
