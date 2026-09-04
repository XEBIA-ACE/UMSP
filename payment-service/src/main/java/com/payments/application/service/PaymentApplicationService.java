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
                .userId(request.getUserId())
                .amount(request.getAmount())
                .currency(request.getCurrency())
                .status(PaymentStatus.PENDING)
                .method(request.getMethod())
                .description(request.getDescription())
                .createdAt(now)
                .updatedAt(now)
                .build();

        // 2. Persist the pending payment
        paymentRepository.save(payment);

        // 3. Delegate to the appropriate gateway
        String transactionId = null;
        boolean success;
        String errorMessage = null;

        if (request.getMethod() == PaymentMethod.STRIPE) {
            StripeGatewayPort.ChargeResult result = stripeGateway.charge(
                    request.getUserId(), request.getAmount(), request.getCurrency(), request.getDescription());
            success = result.isSuccess();
            transactionId = result.getTransactionId();
            errorMessage = result.getErrorMessage();
        } else {
            PayPalGatewayPort.ChargeResult result = payPalGateway.charge(
                    request.getUserId(), request.getAmount(), request.getCurrency(), request.getDescription());
            success = result.isSuccess();
            transactionId = result.getTransactionId();
            errorMessage = result.getErrorMessage();
        }

        // 4. Update payment status based on gateway result
        PaymentStatus finalStatus = success ? PaymentStatus.COMPLETED : PaymentStatus.FAILED;

        Payment updatedPayment = payment.toBuilder()
                .status(finalStatus)
                .gatewayTransactionId(transactionId)
                .updatedAt(LocalDateTime.now())
                .build();

        // 5. Persist the updated payment
        paymentRepository.save(updatedPayment);

        // 6. Send a payment confirmation notification on success
        if (success) {
            notificationPort.sendPaymentConfirmation(updatedPayment);
        }

        // 7. Return a ProcessPaymentResponse
        // TODO: Verify ProcessPaymentResponse constructor/builder API matches target version
        return new ProcessPaymentResponse(
                updatedPayment.getId(),
                updatedPayment.getStatus(),
                transactionId,
                errorMessage);
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public Payment getPayment(String paymentId) {
        return paymentRepository.findById(paymentId)
                .orElseThrow(() -> new IllegalArgumentException("Payment not found: " + paymentId));
    }

    /**
     * {@inheritDoc}
     */
    @Override
    public RefundResponse refund(RefundRequest request) {
        Payment payment = paymentRepository.findById(request.getPaymentId())
                .orElseThrow(() -> new IllegalArgumentException("Payment not found: " + request.getPaymentId()));

        if (payment.getStatus() != PaymentStatus.COMPLETED) {
            throw new IllegalStateException("Only completed payments can be refunded");
        }

        boolean success;
        String errorMessage = null;

        if (payment.getMethod() == PaymentMethod.STRIPE) {
            StripeGatewayPort.RefundResult result = stripeGateway.refund(
                    payment.getGatewayTransactionId(), request.getAmount());
            success = result.isSuccess();
            errorMessage = result.getErrorMessage();
        } else {
            PayPalGatewayPort.RefundResult result = payPalGateway.refund(
                    payment.getGatewayTransactionId(), request.getAmount());
            success = result.isSuccess();
            errorMessage = result.getErrorMessage();
        }

        if (success) {
            Payment refundedPayment = payment.toBuilder()
                    .status(PaymentStatus.REFUNDED)
                    .updatedAt(LocalDateTime.now())
                    .build();
            paymentRepository.save(refundedPayment);
            notificationPort.sendRefundConfirmation(refundedPayment);
        }

        // TODO: Verify RefundResponse constructor/builder API matches target version
        return new RefundResponse(
                payment.getId(),
                success ? PaymentStatus.REFUNDED : PaymentStatus.COMPLETED,
                errorMessage);
    }
}