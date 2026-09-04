package com.payments.domain.ports.outbound;

import com.payments.domain.model.Payment;

/**
 * Outbound port (secondary port) for dispatching payment-related notifications to users.
 *
 * <p>Implementations of this interface are infrastructure adapters (e.g. email, SMS,
 * push notification) and live in the adapters layer. This interface belongs to the
 * domain layer and must not depend on any framework or infrastructure concern.
 */
public interface NotificationPort {

    /**
     * Sends a payment confirmation notification to the specified user.
     *
     * @param userId  the identifier of the user to notify
     * @param payment the completed payment for which confirmation is sent
     */
    void sendPaymentConfirmation(String userId, Payment payment);

    /**
     * Sends a refund confirmation notification to the specified user.
     *
     * @param userId  the identifier of the user to notify
     * @param payment the refunded payment for which confirmation is sent
     */
    void sendRefundConfirmation(String userId, Payment payment);
}
