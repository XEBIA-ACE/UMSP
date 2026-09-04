package com.payments.adapters.inbound.rest;

import com.payments.application.dto.ProcessPaymentRequest;
import com.payments.application.dto.ProcessPaymentResponse;
import com.payments.application.dto.RefundRequest;
import com.payments.application.dto.RefundResponse;
import com.payments.domain.model.Payment;
import com.payments.domain.ports.inbound.GetPaymentUseCase;
import com.payments.domain.ports.inbound.ProcessPaymentUseCase;
import com.payments.domain.ports.inbound.RefundPaymentUseCase;
import jakarta.validation.Valid;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Map;

/**
 * REST adapter that exposes the payment use cases over HTTP.
 *
 * <p>This controller translates HTTP requests into use-case calls and maps
 * domain exceptions to appropriate HTTP status codes. It contains no business
 * logic; all orchestration is delegated to the injected use-case ports.
 *
 * <p>Base path: {@code /api/payments}
 */
@RestController
@RequestMapping("/api/payments")
public class PaymentController {

    private final ProcessPaymentUseCase processPaymentUseCase;
    private final GetPaymentUseCase getPaymentUseCase;
    private final RefundPaymentUseCase refundPaymentUseCase;

    /**
     * Constructs the controller with all required inbound use-case ports.
     *
     * @param processPaymentUseCase use case for processing new payments
     * @param getPaymentUseCase     use case for retrieving existing payments
     * @param refundPaymentUseCase  use case for refunding completed payments
     */
    public PaymentController(
            ProcessPaymentUseCase processPaymentUseCase,
            GetPaymentUseCase getPaymentUseCase,
            RefundPaymentUseCase refundPaymentUseCase) {
        this.processPaymentUseCase = processPaymentUseCase;
        this.getPaymentUseCase = getPaymentUseCase;
        this.refundPaymentUseCase = refundPaymentUseCase;
    }

    /**
     * Processes a new payment.
     *
     * <p>The request body is validated via Bean Validation before the use case is invoked.
     *
     * @param request the payment request payload
     * @return {@code 201 Created} with the {@link ProcessPaymentResponse} on success,
     *         or {@code 400 Bad Request} / {@code 500 Internal Server Error} on failure
     */
    @PostMapping
    public ResponseEntity<?> processPayment(@Valid @RequestBody ProcessPaymentRequest request) {
        try {
            ProcessPaymentResponse response = processPaymentUseCase.process(request);
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest()
                    .body(errorBody(e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(errorBody("An unexpected error occurred: " + e.getMessage()));
        }
    }

    /**
     * Retrieves an existing payment by its unique identifier.
     *
     * @param id the payment identifier extracted from the URL path
     * @return {@code 200 OK} with the {@link Payment} on success,
     *         {@code 404 Not Found} if the payment does not exist,
     *         or {@code 500 Internal Server Error} on unexpected failure
     */
    @GetMapping("/{id}")
    public ResponseEntity<?> getPayment(@PathVariable String id) {
        try {
            Payment payment = getPaymentUseCase.getById(id);
            return ResponseEntity.ok(payment);
        } catch (RuntimeException e) {
            String message = e.getMessage();
            if (message != null && message.startsWith("Payment not found")) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(errorBody(message));
            }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(errorBody("An unexpected error occurred: " + message));
        }
    }

    /**
     * Initiates a refund for a completed payment.
     *
     * @param id      the payment identifier extracted from the URL path
     * @param request the refund request payload (reason, etc.)
     * @return {@code 200 OK} with the {@link RefundResponse} on success,
     *         {@code 400 Bad Request} if the payment cannot be refunded,
     *         {@code 404 Not Found} if the payment does not exist,
     *         or {@code 500 Internal Server Error} on unexpected failure
     */
    @PostMapping("/{id}/refund")
    public ResponseEntity<?> refundPayment(
            @PathVariable String id,
            @RequestBody RefundRequest request) {
        try {
            // Ensure the path variable and body are consistent
            RefundRequest effectiveRequest = new RefundRequest(id, request.reason());
            RefundResponse response = refundPaymentUseCase.refund(effectiveRequest);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            String message = e.getMessage();
            if (message != null && message.startsWith("Payment not found")) {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                        .body(errorBody(message));
            }
            if (message != null && message.contains("cannot be refunded")) {
                return ResponseEntity.badRequest()
                        .body(errorBody(message));
            }
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(errorBody("An unexpected error occurred: " + message));
        }
    }

    // ---------------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------------

    /**
     * Builds a simple error response body map.
     *
     * @param message the error message
     * @return a map with a single {@code "error"} key
     */
    private Map<String, String> errorBody(String message) {
        return Map.of("error", message != null ? message : "Unknown error");
    }
}
