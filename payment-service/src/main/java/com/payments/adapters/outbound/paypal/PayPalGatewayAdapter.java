package com.payments.adapters.outbound.paypal;

import com.payments.domain.ports.outbound.PayPalGatewayPort;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.UUID;

/**
 * Outbound adapter that delegates payment charges to the PayPal gateway.
 *
 * <p>This adapter implements {@link PayPalGatewayPort}. The current implementation
 * is a <strong>stub</strong> that logs the charge parameters and returns a mock
 * successful result. It is intended as a starting point for integrating the real
 * PayPal Checkout SDK.
 *
 * <p>TODO: Replace the stub implementation with real PayPal SDK calls:
 * <ol>
 *   <li>Build an {@code OrderRequest} using the PayPal Checkout SDK.</li>
 *   <li>Call {@code ordersController.ordersCreate()} to create the order.</li>
 *   <li>Capture the order via {@code ordersController.ordersCapture()}.</li>
 *   <li>Map the SDK response to a {@link ChargeResult}.</li>
 * </ol>
 */
@Component
public class PayPalGatewayAdapter implements PayPalGatewayPort {

    private static final Logger log = LoggerFactory.getLogger(PayPalGatewayAdapter.class);

    private final String clientId;
    private final String clientSecret;
    private final String mode;

    /**
     * Constructs the adapter with PayPal credentials and operating mode.
     *
     * @param clientId     the PayPal application client id, injected from
     *                     {@code paypal.client.id}
     * @param clientSecret the PayPal application client secret, injected from
     *                     {@code paypal.client.secret}
     * @param mode         the PayPal environment mode ({@code sandbox} or {@code live}),
     *                     injected from {@code paypal.mode} (defaults to {@code sandbox})
     */
    public PayPalGatewayAdapter(
            @Value("${paypal.client.id}") String clientId,
            @Value("${paypal.client.secret}") String clientSecret,
            @Value("${paypal.mode:sandbox}") String mode) {
        this.clientId = clientId;
        this.clientSecret = clientSecret;
        this.mode = mode;
    }

    /**
     * {@inheritDoc}
     *
     * <p><strong>Stub implementation</strong> – logs the charge parameters and returns
     * a mock successful {@link ChargeResult} with a randomly generated transaction id.
     *
     * <p>TODO: Implement real PayPal SDK integration (see class-level Javadoc).
     */
    @Override
    public ChargeResult charge(
            String userId,
            BigDecimal amount,
            String currency,
            String description) {

        log.info(
                "PayPal charge requested [mode={}, userId={}, amount={} {}, description='{}'] "
                        + "– STUB: returning mock success",
                mode, userId, amount, currency, description);

        // TODO: Replace with real PayPal Checkout SDK integration
        // Example flow:
        //   PayPalHttpClient client = new PayPalHttpClient(
        //       mode.equals("live") ? new LiveEnvironment(clientId, clientSecret)
        //                           : new SandboxEnvironment(clientId, clientSecret));
        //   OrdersCreateRequest request = new OrdersCreateRequest();
        //   ... build order body ...
        //   HttpResponse<Order> response = client.execute(request);
        //   return new ChargeResult(response.result().id(), true, null);

        String mockTransactionId = "PAYPAL-MOCK-" + UUID.randomUUID();
        return new ChargeResult(mockTransactionId, true, null);
    }
}
