package com.payments.domain.ports.inbound;

import com.payments.application.dto.ProcessPaymentRequest;
import com.payments.application.dto.ProcessPaymentResponse;

/**
 * Inbound port (primary port) for processing a new payment.
 *
 * <p>Implementations of this interface orchestrate the payment lifecycle:
 * validating the request, delegating to the appropriate gateway, persisting
 * the result, and dispatching notifications.
 *
 * <p>This interface belongs to the domain layer and must not depend on any
 * framework or infrastructure concern.
 */
public interface ProcessPaymentUseCase {

    /**
     * Processes a payment request end-to-end.
     *
     * @param request the validated payment request containing user, amount,
     *                currency, method, and description
     * @return a {@link ProcessPaymentResponse} describing the outcome
     * @throws RuntimeException if the payment cannot be processed
     */
    ProcessPaymentResponse process(ProcessPaymentRequest request);
}
