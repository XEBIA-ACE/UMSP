package com.payments.infrastructure.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;

/**
 * Spring Security configuration for the payment service.
 *
 * <p>Security rules applied:
 * <ul>
 *   <li>{@code /api/health/**} – publicly accessible without authentication (liveness probes).</li>
 *   <li>{@code /api/payments/**} – requires a valid JWT bearer token.</li>
 *   <li>CSRF protection is disabled because the API is stateless and consumed by
 *       non-browser clients.</li>
 *   <li>Session management is set to {@link SessionCreationPolicy#STATELESS} – no
 *       HTTP session is created or used.</li>
 *   <li>JWT validation is delegated to the configured OAuth2 resource server
 *       ({@code spring.security.oauth2.resourceserver.jwt.issuer-uri}).</li>
 * </ul>
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    /**
     * Configures the {@link SecurityFilterChain} for the application.
     *
     * @param http the {@link HttpSecurity} builder provided by Spring Security
     * @return the configured {@link SecurityFilterChain}
     * @throws Exception if the security configuration cannot be applied
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // Disable CSRF – not needed for stateless REST APIs
            .csrf(csrf -> csrf.disable())

            // Define authorisation rules
            .authorizeHttpRequests(auth -> auth
                // Health endpoint is public (no authentication required)
                .requestMatchers("/api/health/**").permitAll()
                // All payment endpoints require a valid JWT
                .requestMatchers("/api/payments/**").authenticated()
                // Deny everything else by default
                .anyRequest().denyAll()
            )

            // Stateless session – no HttpSession will be created
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )

            // OAuth2 resource server with JWT bearer token validation
            .oauth2ResourceServer(oauth2 ->
                oauth2.jwt(Customizer.withDefaults())
            );

        return http.build();
    }
}
