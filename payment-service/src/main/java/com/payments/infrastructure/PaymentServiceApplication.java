package com.payments.infrastructure;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Entry point for the Payment Service Spring Boot application.
 *
 * <p>This class bootstraps the Spring application context. The
 * {@link SpringBootApplication} annotation enables:
 * <ul>
 *   <li>Auto-configuration ({@code @EnableAutoConfiguration})</li>
 *   <li>Component scanning from the {@code com.payments} base package</li>
 *   <li>Configuration class support ({@code @Configuration})</li>
 * </ul>
 *
 * <p>The component scan covers all sub-packages under {@code com.payments},
 * including {@code domain}, {@code application}, {@code adapters}, and
 * {@code infrastructure}, ensuring that all Spring-managed beans are discovered.
 */
@SpringBootApplication(scanBasePackages = "com.payments")
public class PaymentServiceApplication {

    /**
     * Application entry point.
     *
     * @param args command-line arguments passed to the JVM
     */
    public static void main(String[] args) {
        SpringApplication.run(PaymentServiceApplication.class, args);
    }
}
