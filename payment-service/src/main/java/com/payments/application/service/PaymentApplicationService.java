package com.payments.application.service;

import com.payments.application.dto.ProcessPaymentRequest;
import com.payments.application.dto.ProcessPaymentResponse;
import com.payments.application.dto.RefundRequest;
import com.payments.application.dto.RefundResponse;
import com.payments.domain.model.Payment;
import com.payments.domain.model.PaymentMethod;
import com.payments.domain.model.PaymentStatus;
import com.payments.domain.ports.inbound.GetPaymentUseCase;
import com.payments.domain.ports.inbound.ProcessPaymentUseCase;
import com.payments.domain.ports.inbound.RefundPaymentUseCase;
import com.payments.domain.ports.outbound.NotificationPort;
import com.payments.domain.ports.outbound.PayPalGatewayPort;
import com.payments.domain.ports.outbound.PaymentRepositoryPort;
import com.payments.domain.ports.outbound.StripeGatewayPort;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.UUID;

/**
 * Core application service that orchestrates payment processing, retrieval, and refunds.
 *
 * <p>This class implements all three inbound use-case ports and depends exclusively on
 * outbound port interfaces, keeping it free of any infrastructure concern. It is the
 * single authoritative place for payment business logic.
 *
 * <p>Dependencies are injected via constructor to facilitate unit testing with mocks.
 */
@Service
public class PaymentApplicationService
        implements ProcessPaymentUseCase, GetPaymentUseCase, RefundPaymentUseCase {

    private final PaymentRepositoryPort paymentRepository;
    private final StripeGatewayPort stripeGateway;
    private final PayPalGatewayPort payPalGateway;
    private final NotificationPort notificationPort;

    /**
     * Constructs the service with all required outbound port adapters.
     *
     * @param paymentRepository the persistence adapter
     * @param stripeGateway     the Stripe gateway adapter
     * @param payPalGateway     the PayPal gateway adapter
     * @param notificationPort  the notification adapter
     */
    public PaymentApplicationService(
            PaymentRepositoryPort paymentRepository,
            StripeGatewayPort stripeGateway,
            PayPalGatewayPort payPalGateway,
            NotificationPort notificationPort) {
        this.paymentRepository = paymentRepository;
        this.stripeGateway = stripeGateway;
        this.payPalGateway = payPalGateway;
        this.notificationPort = notificationPort;
    }

    /**
     * {@inheritDoc}
     *
     * <p>Processing steps:
     * <ol>
     *   <li>Create a {@link Payment} with {@link PaymentStatus#PENDING} status.</li>
     *   <li>Persist the pending payment.</li>
     *   <li>Route to the appropriate gateway (Stripe or PayPal).</li>
     *   <li>Update the payment status to {@link PaymentStatus#COMPLETED} or
     *       {@link PaymentStatus#FAILED} based on the gateway result.</li>
     *   <li>Persist the updated payment.</li>
     *   <li>Send a payment confirmation notification on success.</li>
     *   <li>Return a {@link ProcessPaymentResponse}.</li>
     * </ol>
     */
    @Override
    public ProcessPaymentResponse process(ProcessPaymentRequest request) {
        // 1. Build a new Payment in PENDING state
        String paymentId = UUID.randomUUID().toString();
        LocalDateTime now = LocalDateTime.now();

        Payment payment = Payment.builder()
                .id(paymentId)
                .userId(request.userId())
                .amount(request.amount())
                .currency(request.currency())
                .status(PaymentStatus.PENDING)
                .method(request.method())
                .description(request.description())
                .createdAt(now)
                .updatedAt(now)
                .build();

        // 2. Persist the pending payment
        paymentRepository.save(payment);

        // 3. Delegate to the appropriate gateway
        String transactionId = null;
        boolean success;
        String errorMessage = null;

        if (request.method() == PaymentMethod.STRIPE) {
            StripeGatewayPort.ChargeResult result = stripeGateway.charge(
                    request.userId(), request.amount(), request.currency(), request.description());
            success = result.success();
            transactionId = result.transactionId();
            errorMessage = result.errorMessage();
        } else {
            PayPalGatewayPort.ChargeResult result = payPalGateway.charge(
                    request.userId(), request.amount(), request.currency(), request.description());
            success = result.success();
            transactionId = result.transactionId();
            errorMessage = result.errorMessage();
        }

        // 4. Update payment status based on gateway result
        PaymentStatus finalStatus = success ? PaymentStatus.COMPLETED : PaymentStatus.FAILED;

        Payment updatedPayment = payment.toBuilder()
                .status(finalStatus)
                .gatewayTransactionId(transactionId)
                .updatedAt(LocalDateTime.now())
                .build();

        // 5. Persist the updated payment
        paymentRepository.update(updatedPayment);

        // 6. Send notification on success
        if (success) {
            notificationPort.sendPaymentConfirmation(request.userId(), updatedPayment);
        }

        // 7. Return response
        String message = success
                ? "Payment processed successfully"
                : "Payment failed: " + errorMessage;

        return new ProcessPaymentResponse(paymentId, finalStatus, transactionId, message);
    }

    /**
     * {@inheritDoc}
     *
     * @throws RuntimeException if no payment with the given {@code id} exists
     */
    @Override
    public Payment getById(String id) {
        return paymentRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Payment not found: " + id));
    }

    /**
     * {@inheritDoc}
     *
     * <p>Refund steps:
     * <ol>
     *   <li>Retrieve the payment; throw if not found.</li>
     *   <li>Validate that the payment status is {@link PaymentStatus#COMPLETED}.</li>
     *   <li>Update the payment status to {@link PaymentStatus#REFUNDED}.</li>
     *   <li>Persist the updated payment.</li>
     *   <li>Send a refund confirmation notification.</li>
     *   <li>Return a {@link RefundResponse}.</li>
     * </ol>
     *
     * @throws RuntimeException if the payment is not found or is not in COMPLETED status
     */
    @Override
    public RefundResponse refund(RefundRequest request) {
        // 1. Retrieve the payment
        Payment payment = paymentRepository.findById(request.paymentId())
                .orElseThrow(() -> new RuntimeException("Payment not found: " + request.paymentId()));

        // 2. Validate status
        if (payment.getStatus() != PaymentStatus.COMPLETED) {
            throw new RuntimeException(
                    "Payment " + request.paymentId() + " cannot be refunded: current status is "
                            + payment.getStatus());
        }

        // 3. Update to REFUNDED
        Payment refundedPayment = payment.toBuilder()
                .status(PaymentStatus.REFUNDED)
                .updatedAt(LocalDateTime.now())
                .build();

        // 4. Persist
        paymentRepository.update(refundedPayment);

        // 5. Notify
        notificationPort.sendRefundConfirmation(payment.getUserId(), refundedPayment);

        // 6. Return response
        return new RefundResponse(
                request.paymentId(),
                PaymentStatus.REFUNDED,
                "Refund processed successfully");
    }
}
