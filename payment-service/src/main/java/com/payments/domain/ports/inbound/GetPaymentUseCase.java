package com.payments.domain.ports.inbound;

import com.payments.domain.model.Payment;

/**
 * Inbound port (primary port) for retrieving an existing payment by its identifier.
 *
 * <p>This interface belongs to the domain layer and must not depend on any
 * framework or infrastructure concern.
 */
public interface GetPaymentUseCase {

    /**
     * Retrieves a {@link Payment} by its unique identifier.
     *
     * @param id the unique payment identifier
     * @return the matching {@link Payment}
     * @throws RuntimeException if no payment with the given {@code id} exists
     */
    Payment getById(String id);
}
