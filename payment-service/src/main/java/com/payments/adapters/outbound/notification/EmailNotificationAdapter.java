package com.payments.adapters.outbound.notification;

import com.payments.domain.model.Payment;
import com.payments.domain.ports.outbound.NotificationPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

/**
 * Outbound adapter that sends payment-related notifications via email.
 *
 * <p>When {@code notification.email.enabled} is {@code false} (the default), this
 * adapter only logs the notification details and does not attempt any real delivery.
 * This makes it safe to run in development and test environments without an SMTP
 * server.
 *
 * <p>TODO: Replace the stub implementation with a real email integration:
 * <ol>
 *   <li>Add {@code spring-boot-starter-mail} to the POM.</li>
 *   <li>Configure {@code spring.mail.*} properties.</li>
 *   <li>Inject {@code JavaMailSender} and build a {@code MimeMessage}.</li>
 *   <li>Use a template engine (e.g. Thymeleaf) for HTML email bodies.</li>
 * </ol>
 */
@Component
public class EmailNotificationAdapter implements NotificationPort {

    private static final Logger log = LoggerFactory.getLogger(EmailNotificationAdapter.class);

    private final boolean enabled;

    /**
     * Constructs the adapter.
     *
     * @param enabled whether real email delivery is enabled, injected from
     *                {@code notification.email.enabled} (defaults to {@code false})
     */
    public EmailNotificationAdapter(
            @Value("${notification.email.enabled:false}") boolean enabled) {
        this.enabled = enabled;
    }

    /**
     * {@inheritDoc}
     *
     * <p>Logs the confirmation details. If {@code notification.email.enabled} is
     * {@code true}, a real email would be sent here (TODO).
     */
    @Override
    public void sendPaymentConfirmation(String userId, Payment payment) {
        log.info(
                "Payment confirmation notification [userId={}, paymentId={}, amount={} {}, "
                        + "status={}, gatewayTxId={}]",
                userId,
                payment.getId(),
                payment.getAmount(),
                payment.getCurrency(),
                payment.getStatus(),
                payment.getGatewayTransactionId());

        if (enabled) {
            // TODO: Implement real email delivery
            // Example:
            //   MimeMessage message = mailSender.createMimeMessage();
            //   MimeMessageHelper helper = new MimeMessageHelper(message, true);
            //   helper.setTo(resolveEmailAddress(userId));
            //   helper.setSubject("Payment Confirmation – " + payment.getId());
            //   helper.setText(buildConfirmationBody(payment), true);
            //   mailSender.send(message);
            log.warn("Email sending is enabled but not yet implemented – skipping delivery.");
        } else {
            log.debug("Email notifications disabled – skipping delivery for payment {}.",
                    payment.getId());
        }
    }

    /**
     * {@inheritDoc}
     *
     * <p>Logs the refund details. If {@code notification.email.enabled} is
     * {@code true}, a real email would be sent here (TODO).
     */
    @Override
    public void sendRefundConfirmation(String userId, Payment payment) {
        log.info(
                "Refund confirmation notification [userId={}, paymentId={}, amount={} {}, "
                        + "status={}]",
                userId,
                payment.getId(),
                payment.getAmount(),
                payment.getCurrency(),
                payment.getStatus());

        if (enabled) {
            // TODO: Implement real email delivery
            // Example:
            //   MimeMessage message = mailSender.createMimeMessage();
            //   MimeMessageHelper helper = new MimeMessageHelper(message, true);
            //   helper.setTo(resolveEmailAddress(userId));
            //   helper.setSubject("Refund Confirmation – " + payment.getId());
            //   helper.setText(buildRefundBody(payment), true);
            //   mailSender.send(message);
            log.warn("Email sending is enabled but not yet implemented – skipping delivery.");
        } else {
            log.debug("Email notifications disabled – skipping delivery for payment {}.",
                    payment.getId());
        }
    }
}
