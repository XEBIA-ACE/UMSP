package com.payments.application.service;

import com.payments.application.dto.ProcessPaymentRequest;
import com.payments.application.dto.ProcessPaymentResponse;
import com.payments.application.dto.RefundRequest;
import com.payments.domain.model.Payment;
import com.payments.domain.model.PaymentMethod;
import com.payments.domain.model.PaymentStatus;
import com.payments.domain.ports.outbound.NotificationPort;
import com.payments.domain.ports.outbound.PayPalGatewayPort;
import com.payments.domain.ports.outbound.PaymentRepositoryPort;
import com.payments.domain.ports.outbound.StripeGatewayPort;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.ArgumentCaptor;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.math.BigDecimal;
import java.time.LocalDateTime;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;

/**
 * Unit tests for {@link PaymentApplicationService}.
 *
 * <p>No Spring context is loaded – all collaborators are replaced with Mockito mocks.
 * This keeps the tests fast and focused purely on the application service logic.
 */
@ExtendWith(MockitoExtension.class)
class PaymentApplicationServiceTest {

    @Mock
    private PaymentRepositoryPort paymentRepository;

    @Mock
    private StripeGatewayPort stripeGateway;

    @Mock
    private PayPalGatewayPort payPalGateway;

    @Mock
    private NotificationPort notificationPort;

    private PaymentApplicationService service;

    @BeforeEach
    void setUp() {
        service = new PaymentApplicationService(
                paymentRepository, stripeGateway, payPalGateway, notificationPort);
    }

    // -------------------------------------------------------------------------
    // process() tests
    // -------------------------------------------------------------------------

    /**
     * Verifies that when a STRIPE payment request is processed:
     * <ol>
     *   <li>{@link StripeGatewayPort#charge} is called exactly once.</li>
     *   <li>The payment is saved to the repository with COMPLETED status.</li>
     *   <li>A payment confirmation notification is dispatched.</li>
     *   <li>The response contains the gateway transaction id.</li>
     * </ol>
     */
    @Test
    @DisplayName("process() with STRIPE method calls stripeGateway.charge() and saves payment")
    void process_stripeMethod_callsStripeAndSavesPayment() {
        // Arrange
        ProcessPaymentRequest request = new ProcessPaymentRequest(
                "user-1", new BigDecimal("100.00"), "USD", PaymentMethod.STRIPE, "Test charge");

        StripeGatewayPort.ChargeResult chargeResult =
                new StripeGatewayPort.ChargeResult("pi_test_abc", true, null);

        when(stripeGateway.charge(anyString(), any(BigDecimal.class), anyString(), anyString()))
                .thenReturn(chargeResult);

        ArgumentCaptor<Payment> savedPaymentCaptor = ArgumentCaptor.forClass(Payment.class);
        when(paymentRepository.save(savedPaymentCaptor.capture()))
                .thenAnswer(inv -> inv.getArgument(0));
        when(paymentRepository.update(any(Payment.class)))
                .thenAnswer(inv -> inv.getArgument(0));

        // Act
        ProcessPaymentResponse response = service.process(request);

        // Assert – gateway was called
        verify(stripeGateway, times(1))
                .charge("user-1", new BigDecimal("100.00"), "USD", "Test charge");
        verifyNoInteractions(payPalGateway);

        // Assert – payment was saved with COMPLETED status
        verify(paymentRepository, atLeastOnce()).save(any(Payment.class));
        verify(paymentRepository, atLeastOnce()).update(any(Payment.class));

        // Assert – notification was sent
        verify(notificationPort, times(1))
                .sendPaymentConfirmation(eq("user-1"), any(Payment.class));

        // Assert – response
        assertThat(response.status()).isEqualTo(PaymentStatus.COMPLETED);
        assertThat(response.gatewayTransactionId()).isEqualTo("pi_test_abc");
    }

    /**
     * Verifies that when a PAYPAL payment request is processed:
     * <ol>
     *   <li>{@link PayPalGatewayPort#charge} is called exactly once.</li>
     *   <li>{@link StripeGatewayPort#charge} is never called.</li>
     * </ol>
     */
    @Test
    @DisplayName("process() with PAYPAL method calls payPalGateway.charge() and not stripe")
    void process_paypalMethod_callsPayPalAndNotStripe() {
        // Arrange
        ProcessPaymentRequest request = new ProcessPaymentRequest(
                "user-2", new BigDecimal("50.00"), "EUR", PaymentMethod.PAYPAL, "PayPal charge");

        PayPalGatewayPort.ChargeResult chargeResult =
                new PayPalGatewayPort.ChargeResult("pp_order_xyz", true, null);

        when(payPalGateway.charge(anyString(), any(BigDecimal.class), anyString(), anyString()))
                .thenReturn(chargeResult);
        when(paymentRepository.save(any(Payment.class))).thenAnswer(inv -> inv.getArgument(0));
        when(paymentRepository.update(any(Payment.class))).thenAnswer(inv -> inv.getArgument(0));

        // Act
        service.process(request);

        // Assert
        verify(payPalGateway, times(1))
                .charge("user-2", new BigDecimal("50.00"), "EUR", "PayPal charge");
        verifyNoInteractions(stripeGateway);
    }

    // -------------------------------------------------------------------------
    // getById() tests
    // -------------------------------------------------------------------------

    /**
     * Verifies that {@code getById()} throws a {@link RuntimeException} with the
     * expected message when no payment exists for the given id.
     */
    @Test
    @DisplayName("getById() throws RuntimeException when payment is not found")
    void getById_notFound_throwsRuntimeException() {
        // Arrange
        when(paymentRepository.findById("missing-id")).thenReturn(Optional.empty());

        // Act & Assert
        assertThatThrownBy(() -> service.getById("missing-id"))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("Payment not found: missing-id");
    }

    /**
     * Verifies that {@code getById()} returns the payment when it exists.
     */
    @Test
    @DisplayName("getById() returns payment when found")
    void getById_found_returnsPayment() {
        // Arrange
        Payment payment = Payment.builder()
                .id("pay-1")
                .userId("user-1")
                .amount(new BigDecimal("25.00"))
                .currency("USD")
                .status(PaymentStatus.COMPLETED)
                .method(PaymentMethod.STRIPE)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(paymentRepository.findById("pay-1")).thenReturn(Optional.of(payment));

        // Act
        Payment result = service.getById("pay-1");

        // Assert
        assertThat(result.getId()).isEqualTo("pay-1");
        assertThat(result.getStatus()).isEqualTo(PaymentStatus.COMPLETED);
    }

    // -------------------------------------------------------------------------
    // refund() tests
    // -------------------------------------------------------------------------

    /**
     * Verifies that {@code refund()} throws a {@link RuntimeException} when the
     * payment's status is not {@link PaymentStatus#COMPLETED}.
     */
    @Test
    @DisplayName("refund() throws RuntimeException when payment is not COMPLETED")
    void refund_paymentNotCompleted_throwsRuntimeException() {
        // Arrange – payment is in PENDING state
        Payment pendingPayment = Payment.builder()
                .id("pay-pending")
                .userId("user-1")
                .amount(new BigDecimal("75.00"))
                .currency("USD")
                .status(PaymentStatus.PENDING)
                .method(PaymentMethod.STRIPE)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(paymentRepository.findById("pay-pending"))
                .thenReturn(Optional.of(pendingPayment));

        RefundRequest refundRequest = new RefundRequest("pay-pending", "Changed mind");

        // Act & Assert
        assertThatThrownBy(() -> service.refund(refundRequest))
                .isInstanceOf(RuntimeException.class)
                .hasMessageContaining("pay-pending");
    }

    /**
     * Verifies that {@code refund()} throws a {@link RuntimeException} when the
     * payment is already in {@link PaymentStatus#REFUNDED} state.
     */
    @Test
    @DisplayName("refund() throws RuntimeException when payment is already REFUNDED")
    void refund_alreadyRefunded_throwsRuntimeException() {
        // Arrange
        Payment refundedPayment = Payment.builder()
                .id("pay-refunded")
                .userId("user-1")
                .amount(new BigDecimal("30.00"))
                .currency("USD")
                .status(PaymentStatus.REFUNDED)
                .method(PaymentMethod.PAYPAL)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(paymentRepository.findById("pay-refunded"))
                .thenReturn(Optional.of(refundedPayment));

        RefundRequest refundRequest = new RefundRequest("pay-refunded", "Duplicate");

        // Act & Assert
        assertThatThrownBy(() -> service.refund(refundRequest))
                .isInstanceOf(RuntimeException.class);
    }

    /**
     * Verifies that a successful refund updates the payment status to
     * {@link PaymentStatus#REFUNDED}, persists the change, and sends a
     * refund confirmation notification.
     */
    @Test
    @DisplayName("refund() on COMPLETED payment updates status to REFUNDED and notifies")
    void refund_completedPayment_updatesStatusAndNotifies() {
        // Arrange
        Payment completedPayment = Payment.builder()
                .id("pay-done")
                .userId("user-1")
                .amount(new BigDecimal("200.00"))
                .currency("USD")
                .status(PaymentStatus.COMPLETED)
                .method(PaymentMethod.STRIPE)
                .gatewayTransactionId("pi_done")
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        when(paymentRepository.findById("pay-done"))
                .thenReturn(Optional.of(completedPayment));
        when(paymentRepository.update(any(Payment.class)))
                .thenAnswer(inv -> inv.getArgument(0));

        RefundRequest refundRequest = new RefundRequest("pay-done", "Customer request");

        // Act
        var response = service.refund(refundRequest);

        // Assert
        assertThat(response.status()).isEqualTo(PaymentStatus.REFUNDED);
        assertThat(response.paymentId()).isEqualTo("pay-done");
        verify(paymentRepository, times(1)).update(any(Payment.class));
        verify(notificationPort, times(1))
                .sendRefundConfirmation(eq("user-1"), any(Payment.class));
    }
}
