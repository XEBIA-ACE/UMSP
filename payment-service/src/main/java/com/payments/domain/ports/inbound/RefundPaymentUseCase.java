package com.payments.domain.ports.inbound;

import com.payments.application.dto.RefundRequest;
import com.payments.application.dto.RefundResponse;

/**
 * Inbound port (primary port) for refunding a previously completed payment.
 *
 * <p>This interface belongs to the domain layer and must not depend on any
 * framework or infrastructure concern.
 */
public interface RefundPaymentUseCase {

    /**
     * Initiates a refund for a completed payment.
     *
     * @param request the refund request containing the payment identifier and reason
     * @return a {@link RefundResponse} describing the outcome
     * @throws RuntimeException if the payment cannot be refunded (e.g. not found,
     *                          wrong status, or gateway error)
     */
    RefundResponse refund(RefundRequest request);
}
