// =============================================================================
// MigrationCompatibilityShim.java
// Shopizer — Spring Boot 2.5.x → 3.3.x / Jakarta EE Migration Helper
//
// Addresses breaking changes from:
//   - Spring Boot 2.5.12 → 3.3.x (javax.* → jakarta.* namespace)
//   - Spring Security 5.5.x → 6.3.x
//   - Spring Data JPA 2.5.x → 3.3.x
//   - Springfox 2.9.2 → springdoc-openapi 2.x
//   - Drools 7.32.0.Final → 9.x
//   - Infinispan 9.4.18.Final → 15.x
//   - MapStruct 1.3.0.Final → 1.6.x
//   - jjwt 0.8.0 → 0.12.x
//   - commons-fileupload 1.3.3 → 1.5+
//   - postgresql driver 42.2.18 → 42.7.x
// =============================================================================

package com.shopizer.migration;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jws;
import io.jsonwebtoken.JwtParserBuilder;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.infinispan.Cache;
import org.infinispan.configuration.cache.ConfigurationBuilder;
import org.infinispan.configuration.global.GlobalConfigurationBuilder;
import org.infinispan.manager.DefaultCacheManager;
import org.infinispan.manager.EmbeddedCacheManager;
import org.kie.api.KieServices;
import org.kie.api.builder.KieBuilder;
import org.kie.api.builder.KieFileSystem;
import org.kie.api.builder.KieModule;
import org.kie.api.runtime.KieContainer;
import org.kie.api.runtime.KieSession;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpMethod;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.filter.OncePerRequestFilter;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.multipart.MultipartResolver;
import org.springframework.web.multipart.support.StandardServletMultipartResolver;

import javax.crypto.SecretKey;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.concurrent.TimeUnit;

// =============================================================================
// SECTION 1: javax.* → jakarta.* NAMESPACE MIGRATION SHIM
// =============================================================================
// TODO [MANUAL]: Perform a project-wide find-and-replace of all javax.* imports
//   to jakarta.* across all modules (sm-core, sm-core-model, sm-shop, etc.).
//   Specifically:
//     javax.persistence.*       → jakarta.persistence.*
//     javax.servlet.*           → jakarta.servlet.*
//     javax.validation.*        → jakarta.validation.*
//     javax.transaction.*       → jakarta.transaction.*
//     javax.annotation.*        → jakarta.annotation.*
//     javax.xml.bind.*          → jakarta.xml.bind.*
//   This is required by Spring Boot 3.x (Jakarta EE 10).
//   Reference: Spring Boot 3.0 Migration Guide — "Jakarta EE APIs"
//   Automated tooling: OpenRewrite recipe "org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta"
//   is strongly recommended for the 50 JPA entities in sm-core-model.

// =============================================================================
// SECTION 2: SPRING SECURITY 5.5.x → 6.3.x SHIM
// =============================================================================

/**
 * SecurityConfigShim replaces the deprecated WebSecurityConfigurerAdapter pattern
 * (removed in Spring Security 6.x) with the new SecurityFilterChain bean approach.
 *
 * BREAKING CHANGE: WebSecurityConfigurerAdapter has been removed in Spring Security 6.x.
 * All classes extending WebSecurityConfigurerAdapter must be refactored.
 *
 * TODO [MANUAL]: Locate all classes in sm-shop that extend WebSecurityConfigurerAdapter
 *   and replace them with @Bean SecurityFilterChain methods as shown below.
 *   Reference: Spring Security 6.x — "WebSecurityConfigurerAdapter Removed"
 *
 * TODO [MANUAL]: Replace antMatchers(...) with requestMatchers(...) throughout all
 *   security configuration classes. antMatchers was removed in Spring Security 6.x.
 *   Reference: Spring Security 6.x — "antMatchers, mvcMatchers, regexMatchers removed"
 *
 * TODO [MANUAL]: Replace authorizeRequests() with authorizeHttpRequests() in all
 *   security configuration classes.
 *   Reference: Spring Security 6.x — "authorizeRequests() deprecated and removed"
 *
 * TODO [MANUAL]: Review all uses of HttpSecurity.cors() — the no-arg cors() method
 *   now requires explicit CorsConfigurationSource bean or lambda configuration.
 *   Reference: Spring Security 6.x — "cors() without CorsConfigurationSource"
 */
@Configuration
@EnableWebSecurity
public class MigrationCompatibilityShim {

    private static final Logger log = LoggerFactory.getLogger(MigrationCompatibilityShim.class);

    // =========================================================================
    // SECTION 2.1: SecurityFilterChain (replaces WebSecurityConfigurerAdapter)
    // =========================================================================

    /**
     * Replaces the old pattern:
     *   protected void configure(HttpSecurity http) throws Exception { ... }
     * inside a class extending WebSecurityConfigurerAdapter.
     *
     * TODO [MANUAL]: Inject the actual JwtAuthenticationFilter bean used by Shopizer
     *   (typically com.salesmanager.shop.store.security.JWTTokenFilter or equivalent)
     *   and replace the placeholder JwtAuthenticationFilterShim below.
     *
     * TODO [MANUAL]: Adjust requestMatchers paths to match Shopizer's actual
     *   endpoint patterns (e.g., /api/v1/**, /shop/**, /swagger-ui/**).
     */
    @Bean
    public SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            JwtAuthenticationFilterShim jwtAuthenticationFilterShim) throws Exception {

        http
            // BREAKING CHANGE: csrf().disable() lambda form required in Spring Security 6.x
            .csrf(AbstractHttpConfigurer::disable)

            // BREAKING CHANGE: authorizeRequests() replaced by authorizeHttpRequests()
            // BREAKING CHANGE: antMatchers() replaced by requestMatchers()
            .authorizeHttpRequests(auth -> auth
                // TODO [MANUAL]: Replace these placeholder patterns with Shopizer's
                //   actual public/private endpoint mappings from SecurityConfig.
                .requestMatchers(HttpMethod.GET, "/api/v1/products/**").permitAll()
                .requestMatchers(HttpMethod.GET, "/api/v1/category/**").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/v1/customer/login").permitAll()
                .requestMatchers(HttpMethod.POST, "/api/v1/merchant/login").permitAll()
                .requestMatchers("/swagger-ui/**", "/v3/api-docs/**").permitAll()
                .requestMatchers("/actuator/health").permitAll()
                .anyRequest().authenticated()
            )
            .sessionManagement(session ->
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            // BREAKING CHANGE: cors() now requires explicit lambda or bean
            .cors(cors -> {
                // TODO [MANUAL]: Wire in Shopizer's existing CorsConfigurationSource bean
                //   (e.g., corsConfigurationSource()) to replace the old cors().and() pattern.
            })
            .addFilterBefore(jwtAuthenticationFilterShim,
                UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * PasswordEncoder bean — unchanged API, but must now be declared as a @Bean
     * rather than overriding configure(AuthenticationManagerBuilder) in
     * WebSecurityConfigurerAdapter.
     *
     * TODO [MANUAL]: Ensure no duplicate PasswordEncoder bean exists after removing
     *   WebSecurityConfigurerAdapter subclasses.
     */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // =========================================================================
    // SECTION 3: JJWT 0.8.0 → 0.12.x SHIM
    // =========================================================================

    /**
     * JwtTokenProviderShim wraps the breaking API changes in jjwt 0.8.0 → 0.12.x.
     *
     * BREAKING CHANGES addressed:
     *   - Jwts.parser() replaced by Jwts.parserBuilder() (0.11.x) then Jwts.parser() with
     *     new fluent API in 0.12.x
     *   - setSigningKey(String) removed — must use Keys.hmacShaKeyFor(byte[]) or
     *     Keys.secretKeyFor(SignatureAlgorithm)
     *   - signWith(SignatureAlgorithm, String) removed — use signWith(SecretKey)
     *   - Jwts.builder().setSubject() → subject() in 0.12.x
     *   - Jwts.builder().setExpiration() → expiration() in 0.12.x
     *   - Jwts.builder().setIssuedAt() → issuedAt() in 0.12.x
     *   - parseClaimsJws() → parseSignedClaims() in 0.12.x
     *
     * TODO [MANUAL]: Replace all direct usages of the old JwtTokenProvider in
     *   com.salesmanager.shop.store.security (or equivalent package) with this shim
     *   or refactor inline using the patterns shown here.
     *
     * TODO [MANUAL]: Rotate all JWT signing secrets — algorithm confusion
     *   vulnerabilities in jjwt 0.8.0 (CVE history) mean existing tokens signed
     *   with the old library should be invalidated after upgrade.
     *
     * TODO [MANUAL]: Verify that the configured secret key is at least 256 bits
     *   (32 bytes) for HMAC-SHA256. Keys shorter than the algorithm's minimum
     *   will throw WeakKeyException in jjwt 0.12.x.
     */
    public static class JwtTokenProviderShim {

        private final SecretKey signingKey;
        private final long expirationMs;

        public JwtTokenProviderShim(String base64Secret, long expirationMs) {
            // BREAKING CHANGE: setSigningKey(String) removed.
            // Old: .setSigningKey(secret)
            // New: Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8))
            // TODO [MANUAL]: Ensure base64Secret is at least 32 characters (256 bits)
            //   for HS256. Use a securely generated secret in production.
            this.signingKey = Keys.hmacShaKeyFor(
                base64Secret.getBytes(StandardCharsets.UTF_8)
            );
            this.expirationMs = expirationMs;
        }

        /**
         * Generates a JWT token.
         *
         * BREAKING CHANGE (0.12.x): Builder method renames:
         *   setSubject(s)    → subject(s)
         *   setIssuedAt(d)   → issuedAt(d)
         *   setExpiration(d) → expiration(d)
         *   signWith(alg, key) → signWith(key)  [algorithm inferred from key type]
         */
        public String generateToken(String username, Map<String, Object> claims) {
            Date now = new Date();
            Date expiry = new Date(now.getTime() + expirationMs);

            // TODO [MANUAL]: Add any Shopizer-specific claims (e.g., merchantCode,
            //   roles, storeCode) that were previously set via addClaims() or
            //   setClaims() in the old token provider.
            return Jwts.builder()
                .claims(claims)                    // replaces setClaims() in 0.12.x
                .subject(username)                 // replaces setSubject() in 0.12.x
                .issuedAt(now)                     // replaces setIssuedAt() in 0.12.x
                .expiration(expiry)                // replaces setExpiration() in 0.12.x
                .signWith(signingKey)              // replaces signWith(alg, key) in 0.12.x
                .compact();
        }

        /**
         * Validates and parses a JWT token.
         *
         * BREAKING CHANGE (0.12.x):
         *   Jwts.parserBuilder() → Jwts.parser()  (parserBuilder() removed in 0.12.x)
         *   .parseClaimsJws()   → .parseSignedClaims()
         */
        public Claims parseToken(String token) {
            // BREAKING CHANGE: parserBuilder() was introduced in 0.11.x and removed in 0.12.x.
            // Old (0.8.0):  Jwts.parser().setSigningKey(key).parseClaimsJws(token).getBody()
            // New (0.12.x): Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload()
            JwtParserBuilder parserBuilder = Jwts.parser()
                .verifyWith(signingKey);           // replaces setSigningKey() in 0.12.x

            Jws<Claims> jws = parserBuilder
                .build()
                .parseSignedClaims(token);         // replaces parseClaimsJws() in 0.12.x

            return jws.getPayload();               // replaces .getBody() in 0.12.x
        }

        public String getUsernameFromToken(String token) {
            return parseToken(token).getSubject();
        }

        public boolean isTokenExpired(String token) {
            return parseToken(token).getExpiration().before(new Date());
        }

        public boolean validateToken(String token, String username) {
            return getUsernameFromToken(token).equals(username) && !isTokenExpired(token);
        }
    }

    // =========================================================================
    // SECTION 4: JWT AUTHENTICATION FILTER SHIM
    // =========================================================================

    /**
     * JwtAuthenticationFilterShim replaces any filter that previously extended
     * OncePerRequestFilter using the old jjwt 0.8.0 API.
     *
     * TODO [MANUAL]: Replace the placeholder logic below with Shopizer's actual
     *   UserDetailsService lookup and SecurityContextHolder population pattern
     *   from com.salesmanager.shop.store.security (or equivalent).
     *
     * TODO [MANUAL]: Verify the Authorization header prefix used by Shopizer
     *   (typically "Bearer " — confirm in existing JWTTokenFilter).
     */
    @org.springframework.stereotype.Component
    public static class JwtAuthenticationFilterShim extends OncePerRequestFilter {

        private final JwtTokenProviderShim jwtTokenProvider;
        private final UserDetailsService userDetailsService;

        public JwtAuthenticationFilterShim(
                JwtTokenProviderShim jwtTokenProvider,
                UserDetailsService userDetailsService) {
            this.jwtTokenProvider = jwtTokenProvider;
            this.userDetailsService = userDetailsService;
        }

        @Override
        protected void doFilterInternal(
                HttpServletRequest request,
                HttpServletResponse response,
                FilterChain filterChain) throws ServletException, IOException {

            String authHeader = request.getHeader("Authorization");

            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);
                try {
                    String username = jwtTokenProvider.getUsernameFromToken(token);
                    if (username != null &&
                        org.springframework.security.core.context.SecurityContextHolder
                            .getContext().getAuthentication() == null) {

                        var userDetails = userDetailsService.loadUserByUsername(username);
                        if (jwtTokenProvider.validateToken(token, username)) {
                            var authToken =
                                new org.springframework.security.authentication
                                    .UsernamePasswordAuthenticationToken(
                                        userDetails, null, userDetails.getAuthorities());
                            authToken.setDetails(
                                new org.springframework.security.web.authentication.WebAuthenticationDetailsSource()
                                    .buildDetails(request));
                            org.springframework.security.core.context.SecurityContextHolder
                                .getContext().setAuthentication(authToken);
                        }
                    }
                } catch (Exception e) {
                    log.warn("JWT validation failed: {}", e.getMessage());
                    // TODO [MANUAL]: Align exception handling with Shopizer's existing
                    //   JwtAuthenticationEntryPoint or equivalent error response strategy.
                }
            }
            filterChain.doFilter(request, response);
        }
    }

    // =========================================================================
    // SECTION 5: SPRING DATA JPA 2.5.x → 3.3.x SHIM
    // =========================================================================

    /**
     * SpringDataJpaShim documents and wraps breaking changes in Spring Data JPA 3.x.
     *
     * BREAKING CHANGES:
     *   - CrudRepository.findById() return type unchanged, but JpaRepository.getOne()
     *     has been REMOVED — replaced by getReferenceById()
     *   - Pageable construction: new PageRequest(page, size) removed —
     *     use PageRequest.of(page, size)
     *   - Sort construction: new Sort(direction, properties) removed —
     *     use Sort.by(direction, properties)
     *   - QueryByExampleExecutor API changes
     *   - @EnableJpaRepositories basePackages must be explicit in Spring Boot 3.x
     *     when using multi-module projects
     *
     * TODO [MANUAL]: Search all Shopizer repository classes for .getOne(id) calls
     *   and replace with .getReferenceById(id). getOne() was removed in Spring Data 3.x.
     *   Reference: Spring Data JPA 3.0 — "JpaRepository.getOne removed"
     *
     * TODO [MANUAL]: Search for new PageRequest(page, size) and replace with
     *   PageRequest.of(page, size) throughout sm-core and sm-shop modules.
     *
     * TODO [MANUAL]: Search for new Sort(...) constructors and replace with
     *   Sort.by(...) factory methods.
     *
     * TODO [MANUAL]: Verify that all @Repository interfaces in sm-core-model
     *   are correctly scanned in the multi-module Maven project. Spring Boot 3.x
     *   may require explicit @EnableJpaRepositories(basePackages = "com.salesmanager")
     *   on the main application class or a @Configuration class.
     */
    public static class SpringDataJpaShim {

        @PersistenceContext
        private EntityManager entityManager;

        /**
         * Shim for the removed JpaRepository.getOne(id) method.
         * Old: repository.getOne(id)
         * New: repository.getReferenceById(id)
         *
         * TODO [MANUAL]: Replace all .getOne() calls in Shopizer service classes
         *   with .getReferenceById(). This shim is illustrative only.
         */
        public <T> T getReferenceByIdShim(Class<T> entityClass, Object id) {
            // BREAKING CHANGE: getOne() removed in Spring Data JPA 3.x
            // Old: entityManager.getReference(entityClass, id) was backing getOne()
            // New: getReferenceById() uses the same EntityManager.getReference() internally
            return entityManager.getReference(entityClass, id);
        }

        /**
         * Shim for deprecated PageRequest constructor.
         * Old: new PageRequest(page, size)
         * New: PageRequest.of(page, size)
         */
        public static Pageable createPageable(int page, int size) {
            // BREAKING CHANGE: PageRequest(int, int) constructor removed in Spring Data 3.x
            return PageRequest.of(page, size);
        }

        /**
         * Shim for deprecated PageRequest constructor with Sort.
         * Old: new PageRequest(page, size, Sort.Direction.ASC, "propertyName")
         * New: PageRequest.of(page, size, Sort.by(Sort.Direction.ASC, "propertyName"))
         */
        public static Pageable createPageableWithSort(
                int page, int size, Sort.Direction direction, String... properties) {
            // BREAKING CHANGE: PageRequest(int, int, Sort.Direction, String...) removed
            return PageRequest.of(page, size, Sort.by(direction, properties));
        }
    }

    // =========================================================================
    // SECTION 6: SPRINGFOX 2.9.2 → SPRINGDOC-OPENAPI 2.x MIGRATION SHIM
    // =========================================================================

    /**
     * SpringfoxToSpringdocShim documents the migration from Springfox 2.9.2
     * to springdoc-openapi 2.x.
     *
     * BREAKING CHANGES:
     *   - Springfox is abandoned and incompatible with Spring Boot 3.x
     *   - All Springfox annotations must be replaced with SpringDoc / OpenAPI 3 equivalents
     *   - Docket bean configuration is replaced by OpenAPI bean configuration
     *   - Swagger UI path changes: /swagger-ui.html → /swagger-ui/index.html
     *
     * TODO [MANUAL]: Remove springfox-swagger2 and springfox-swagger-ui dependencies
     *   from all pom.xml files. Add springdoc-openapi-starter-webmvc-ui 2.x instead.
     *   Reference: springdoc-openapi migration guide
     *
     * TODO [MANUAL]: Replace all @Api annotations with @Tag
     *   (import io.swagger.v3.oas.annotations.tags.Tag)
     *
     * TODO [MANUAL]: Replace all @ApiOperation annotations with @Operation
     *   (import io.swagger.v3.oas.annotations.Operation)
     *
     * TODO [MANUAL]: Replace all @ApiParam annotations with @Parameter
     *   (import io.swagger.v3.oas.annotations.Parameter)
     *
     * TODO [MANUAL]: Replace all @ApiResponse / @ApiResponses with
     *   @io.swagger.v3.oas.annotations.responses.ApiResponse /
     *   @io.swagger.v3.oas.annotations.responses.ApiResponses
     *
     * TODO [MANUAL]: Replace all @ApiModel annotations with @Schema
     *   (import io.swagger.v3.oas.annotations.media.Schema)
     *
     * TODO [MANUAL]: Replace all @ApiModelProperty annotations with @Schema
     *   on individual fields.
     *
     * TODO [MANUAL]: Remove the Docket @Bean configuration class entirely.
     *   Replace with an OpenAPI @Bean as shown below.
     *
     * TODO [MANUAL]: Update application.properties/yml:
     *   Old: springfox.documentation.swagger-ui.enabled=true
     *   New: springdoc.swagger-ui.enabled=true
     *        springdoc.api-docs.path=/v3/api-docs
     *        springdoc.swagger-ui.path=/swagger-ui.html  (redirects to /swagger-ui/index.html)
     */
    @Bean
    public io.swagger.v3.oas.models.OpenAPI shopizerOpenAPI() {
        // BREAKING CHANGE: Docket bean (Springfox) replaced by OpenAPI bean (springdoc)
        // Old Springfox Docket pattern:
        //   @Bean public Docket api() {
        //     return new Docket(DocumentationType.SWAGGER_2)
        //       .select()
        //       .apis(RequestHandlerSelectors.basePackage("com.salesmanager"))
        //       .paths(PathSelectors.any())
        //       .build();
        //   }
        //
        // New springdoc-openapi 2.x pattern:
        return new io.swagger.v3.oas.models.OpenAPI()
            .info(new io.swagger.v3.oas.models.info.Info()
                .title("Shopizer REST API")
                .description("Shopizer e-commerce platform API")
                // TODO [MANUAL]: Set the correct API version from Shopizer's existing
                //   Docket configuration or application.properties.
                .version("3.3.x")
                .contact(new io.swagger.v3.oas.models.info.Contact()
                    // TODO [MANUAL]: Populate contact details from existing Springfox config
                    .name("Shopizer")
                    .url("https://www.shopizer.com")))
            .components(new io.swagger.v3.oas.models.Components()
                .addSecuritySchemes("bearerAuth",
                    new io.swagger.v3.oas.models.security.SecurityScheme()
                        .type(io.swagger.v3.oas.models.security.SecurityScheme.Type.HTTP)
                        .scheme("bearer")
                        .bearerFormat("JWT")));
    }

    // =========================================================================
    // SECTION 7: DROOLS 7.32.0.Final → 9.x SHIM
    // =========================================================================

    /**
     * DroolsMigrationShim wraps breaking API changes in Drools 7.x → 9.x.
     *
     * BREAKING CHANGES:
     *   - KieServices, KieContainer, KieSession API largely preserved but
     *     module/classpath scanning behavior changed
     *   - drools-compiler artifact coordinates changed in 9.x
     *   - kie-spring integration replaced — Spring Boot auto-configuration
     *     via drools-spring-boot-starter is no longer available in 9.x
     *   - KieFileSystem / KieBuilder pattern still supported but kmodule.xml
     *     location requirements changed
     *
     * TODO [MANUAL]: Update pom.xml Drools dependency coordinates.
     *   Old groupId: org.drools / org.kie
     *   New groupId: org.drools / org.kie (unchanged in 9.x, but verify BOM)
     *   Old artifactId: drools-core, drools-compiler, kie-spring
     *   New: drools-core, drools-compiler (kie-spring removed — manual wiring required)
     *   Reference: Drools 9.x migration guide — "kie-spring removed"
     *
     * TODO [MANUAL]: Remove kie-spring dependency and manually wire KieContainer
     *   as a Spring @Bean (pattern shown below).
     *
     * TODO [MANUAL]: Verify all .drl rule files in Shopizer's resources directory
     *   are compatible with Drools 9.x syntax. Some deprecated Drools 7.x syntax
     *   may cause compilation errors.
     *
     * TODO [MANUAL]: Review Drools 9.x breaking change — RuleUnitExecutor API
     *   if Shopizer uses rule units (verify in sm-core or sm-shop).
     */
    @Bean
    public KieContainer kieContainer() {
        KieServices kieServices = KieServices.Factory.get();
        KieFileSystem kieFileSystem = kieServices.newKieFileSystem();

        // TODO [MANUAL]: Add all Shopizer .drl rule files here, or configure
        //   kmodule.xml in src/main/resources/META-INF/kmodule.xml.
        //   Old kie-spring auto-scanned classpath rules; this must now be explicit.
        //   Example:
        //   kieFileSystem.write(ResourceFactory.newClassPathResource("rules/pricing.drl"));

        KieBuilder kieBuilder = kieServices.newKieBuilder(kieFileSystem);
        kieBuilder.buildAll();

        KieModule kieModule = kieBuilder.getKieModule();
        return kieServices.newKieContainer(kieModule.getReleaseId());
    }

    /**
     * Shim for KieSession usage — API unchanged but lifecycle management
     * must be explicit in Drools 9.x without kie-spring.
     *
     * TODO [MANUAL]: Replace all Spring-injected KieSession beans (previously
     *   managed by kie-spring) with programmatic session creation as shown here.
     *   Ensure sessions are closed after use to prevent memory leaks.
     */
    public static class DroolsSessionShim {

        private final KieContainer kieContainer;

        public DroolsSessionShim(KieContainer kieContainer) {
            this.kieContainer = kieContainer;
        }

        public void executeRules(Object... facts) {
            // BREAKING CHANGE: kie-spring no longer manages KieSession lifecycle.
            // Sessions must be explicitly created and closed.
            KieSession kieSession = kieContainer.newKieSession();
            try {
                for (Object fact : facts) {
                    kieSession.insert(fact);
                }
                kieSession.fireAllRules();
            } finally {
                kieSession.dispose(); // TODO [MANUAL]: Verify this matches Shopizer's rule execution pattern
            }
        }
    }

    // =========================================================================
    // SECTION 8: INFINISPAN 9.4.18.Final → 15.x SHIM
    // =========================================================================

    /**
     * InfinispanMigrationShim wraps breaking changes in Infinispan 9.x → 15.x.
     *
     * BREAKING CHANGES:
     *   - infinispan-spring-boot-starter coordinates changed
     *   - Configuration XML schema namespace changed (urn:infinispan:config:9.4 → urn:infinispan:config:15.0)
     *   - EmbeddedCacheManager configuration API changes
     *   - Cache.put() with lifespan API unchanged but some eviction config APIs changed
     *   - infinispan-jcache module changes for JCache (JSR-107) integration
     *   - Clustering transport configuration API changed
     *   - org.infinispan.configuration.cache.EvictionConfigurationBuilder removed —
     *     replaced by MemoryConfigurationBuilder
     *
     * TODO [MANUAL]: Update infinispan-spring-boot-starter dependency in pom.xml.
     *   Old: infinispan-spring-boot-starter-embedded 9.4.18.Final
     *   New: infinispan-spring-boot-3-starter-embedded 15.x.x.Final
     *   Reference: Infinispan 15.x migration guide
     *
     * TODO [MANUAL]: Update all Infinispan XML configuration files.
     *   Change namespace: urn:infinispan:config:9.4 → urn:infinispan:config:15.0
     *   Reference: Infinispan 15.x — "Configuration schema changes"
     *
     * TODO [MANUAL]: Replace EvictionConfigurationBuilder usage with
     *   MemoryConfigurationBuilder in all cache configurations.
     *   Old: .eviction().maxEntries(1000).strategy(EvictionStrategy.LRU)
     *   New: .memory().maxCount(1000)
     *   Reference: Infinispan 10.x+ — "Eviction configuration replaced by Memory"
     *
     * TODO [MANUAL]: Review Shopizer's use of Infinispan for session caching,
     *   product caching, and any distributed cache configurations. Verify
     *   serialization compatibility — Infinispan 15.x uses ProtoStream by default
     *   for marshalling, replacing the old JBoss Marshalling default.
     *   Reference: Infinispan 12.x+ — "ProtoStream marshaller as default"
     *
     * TODO [MANUAL]: If Shopizer uses Infinispan's Spring Cache abstraction
     *   (@Cacheable, @CacheEvict), verify that SpringEmbeddedCacheManager or
     *   SpringRemoteCacheManager bean is correctly configured for Infinispan 15.x.
     */
    @Bean
    public EmbeddedCacheManager infinispanCacheManager() {
        GlobalConfigurationBuilder globalConfig = new GlobalConfigurationBuilder();
        // TODO [MANUAL]: Configure transport for clustered mode if Shopizer uses
        //   Infinispan clustering. For embedded/local mode, no transport is needed.
        globalConfig.nonClusteredDefault();

        ConfigurationBuilder cacheConfig = new ConfigurationBuilder();
        // BREAKING CHANGE: .eviction().maxEntries() replaced by .memory().maxCount()
        // Old (9.x): cacheConfig.eviction().maxEntries(1000).strategy(EvictionStrategy.LRU)
        // New (15.x):
        cacheConfig.memory()
            .maxCount(1000L); // replaces eviction().maxEntries()

        // TODO [MANUAL]: Set expiration lifespan to match Shopizer's existing
        //   cache TTL configuration (check infinispan.xml or application.properties).
        cacheConfig.expiration()
            .lifespan(30, TimeUnit.MINUTES)
            .maxIdle(10, TimeUnit.MINUTES);

        DefaultCacheManager cacheManager = new DefaultCacheManager(globalConfig.build());

        // TODO [MANUAL]: Register all named caches used by Shopizer.
        //   Common Shopizer cache names: "shopizer", "products", "categories", "merchants"
        //   Verify actual cache names in Shopizer's existing Infinispan configuration.
        cacheManager.defineConfiguration("shopizer", cacheConfig.build());
        cacheManager.defineConfiguration("products", cacheConfig.build());
        cacheManager.defineConfiguration("categories", cacheConfig.build());

        return cacheManager;
    }

    /**
     * Shim for Infinispan Cache usage — demonstrates API compatibility.
     *
     * TODO [MANUAL]: Verify that all objects stored in Infinispan caches in Shopizer
     *   implement java.io.Serializable OR are annotated with @ProtoField for
     *   ProtoStream marshalling (required in Infinispan 15.x default configuration).
     *   Reference: Infinispan 15.x — "Marshalling and serialization"
     */
    public static class InfinispanCacheShim {

        private final EmbeddedCacheManager cacheManager;

        public InfinispanCacheShim(EmbeddedCacheManager cacheManager) {
            this.cacheManager = cacheManager;
        }

        public <K, V> void put(String cacheName, K key, V value) {
            Cache<K, V> cache = cacheManager.getCache(cacheName);
            cache.put(key, value);
        }

        public <K, V> V get(String cacheName, K key) {
            Cache<K, V> cache = cacheManager.getCache(cacheName);
            return cache.get(key);
        }

        public <K> void evict(String cacheName, K key) {
            Cache<K, ?> cache = cacheManager.getCache(cacheName);
            cache.remove(key);
        }
    }

    // =========================================================================
    // SECTION 9: MAPSTRUCT 1.3.0.Final → 1.6.x SHIM
    // =========================================================================

    /**
     * MapStructMigrationNotes documents breaking changes in MapStruct 1.3.x → 1.6.x.
     *
     * BREAKING CHANGES:
     *   - MapStruct 1.6.x requires Java 11+ (compatible with current JVM 11 target)
     *   - @Mapper(uses = ...) component model changes with Spring
     *   - @BeanMapping(ignoreByDefault = true) behavior refined
     *   - Conditional mapping methods (@Condition) introduced in 1.5.x
     *   - Builder pattern detection improved — may affect existing mappers
     *     that manually handle builders
     *   - @InheritInverseConfiguration behavior changes for complex hierarchies
     *
     * TODO [MANUAL]: Update mapstruct and mapstruct-processor versions in pom.xml.
     *   Old: org.mapstruct:mapstruct:1.3.0.Final
     *        org.mapstruct:mapstruct-processor:1.3.0.Final
     *   New: org.mapstruct:mapstruct:1.6.x
     *        org.mapstruct:mapstruct-processor:1.6.x
     *
     * TODO [MANUAL]: Verify annotationProcessorPaths in maven-compiler-plugin includes
     *   both mapstruct-processor AND lombok-mapstruct-binding (if Lombok is used)
     *   in the correct order. MapStruct 1.6.x is strict about processor ordering.
     *   Reference: MapStruct 1.5.x+ — "Lombok and MapStruct processor ordering"
     *
     * TODO [MANUAL]: Review all @Mapper interfaces in Shopizer for uses of
     *   deprecated mapping methods. Run mvn compile and address all MapStruct
     *   warnings as errors may be introduced in 1.6.x for previously-warned patterns.
     *
     * TODO [MANUAL]: If Shopizer uses @Mapper(componentModel = "spring"), verify
     *   that generated mapper implementations are correctly picked up by Spring Boot 3.x
     *   component scanning after the jakarta.* namespace migration.
     */
    public static class MapStructMigrationNotes {
        // This class is intentionally a documentation placeholder.
        // No runtime shim is possible for annotation processor changes.
        // See TODO comments above for required manual actions.
    }

    // =========================================================================
    // SECTION 10: COMMONS-FILEUPLOAD 1.3.3 → 1.5+ SHIM
    // =========================================================================

    /**
     * FileUploadMigrationShim addresses the migration from commons-fileupload 1.3.3
     * (CVE-2016-1000031 RCE vulnerability) to 1.5+.
     *
     * BREAKING CHANGES:
     *   - commons-fileupload 1.5 introduces DiskFileItemFactory.Builder pattern
     *   - FileUpload streaming API changes in 1.4+
     *   - In Spring Boot 3.x, commons-fileupload is no longer auto-configured —
     *     StandardServletMultipartResolver is the default
     *
     * TODO [MANUAL]: Remove commons-fileupload dependency from pom.xml if Shopizer
     *   only uses it transitively through Spring. Spring Boot 3.x uses
     *   StandardServletMultipartResolver by default (no commons-fileupload needed).
     *
     * TODO [MANUAL]: If Shopizer directly uses CommonsMultipartResolver, replace it
     *   with StandardServletMultipartResolver (shown below).
     *   Old: CommonsMultipartResolver (requires commons-fileupload)
     *   New: StandardServletMultipartResolver (built into Spring, no extra dependency)
     *
     * TODO [MANUAL]: If Shopizer uses DiskFileItemFactory directly (outside of Spring),
     *   update to the builder pattern introduced in commons-fileupload 1.5:
     *   Old: new DiskFileItemFactory(sizeThreshold, repository)
     *   New: DiskFileItemFactory.builder().setSizeThreshold(n).setFile(repository).get()
     *
     * TODO [MANUAL]: Verify multipart configuration in application.properties:
     *   spring.servlet.multipart.enabled=true
     *   spring.servlet.multipart.max-file-size=10MB
     *   spring.servlet.multipart.max-request-size=10MB
     *   (These replace the old CommonsMultipartResolver bean properties)
     */
    @Bean
    public MultipartResolver multipartResolver() {
        // BREAKING CHANGE: CommonsMultipartResolver removed from Spring Boot 3.x auto-config.
        // Replace with StandardServletMultipartResolver.
        // Old: return new CommonsMultipartResolver();
        // New:
        return new StandardServletMultipartResolver();
    }

    /**
     * Shim for handling MultipartFile in controllers — API unchanged in Spring,
     * but underlying implementation no longer uses commons-fileupload.
     *
     * TODO [MANUAL]: Verify all Shopizer file upload controllers (product images,
     *   merchant logos, etc.) use Spring's MultipartFile interface rather than
     *   directly using commons-fileupload FileItem. If FileItem is used directly,
     *   refactor to MultipartFile.
     */
    public static class MultipartFileShim {

        public static byte[] getFileBytes(MultipartFile file) throws IOException {
            // API unchanged — MultipartFile.getBytes() works in Spring Boot 3.x
            return file.getBytes();
        }

        public static String getOriginalFilename(MultipartFile file) {
            // API unchanged
            return file.getOriginalFilename();
        }
    }

    // =========================================================================
    // SECTION 11: POSTGRESQL DRIVER 42.2.18 → 42.7.x SHIM
    // =========================================================================

    /**
     * PostgresqlDriverMigrationNotes documents the upgrade from postgresql 42.2.18
     * (CVE-2022-21724 SQL injection via connection properties) to 42.7.x.
     *
     * BREAKING CHANGES:
     *   - Driver class name unchanged: org.postgresql.Driver
     *   - JDBC URL format unchanged
     *   - Connection property validation is now stricter in 42.7.x —
     *     unknown/invalid properties may cause connection failures
     *   - SSL configuration properties changed in 42.3.x+
     *
     * TODO [MANUAL]: Update postgresql driver version in pom.xml.
     *   Old: org.postgresql:postgresql:42.2.18
     *   New: org.postgresql:postgresql:42.7.x (latest stable)
     *   This is a CRITICAL security fix for CVE-2022-21724.
     *
     * TODO [MANUAL]: Review all JDBC connection URLs and DataSource configurations
     *   in application.properties / application.yml for any connection properties
     *   that may be rejected by the stricter validation in 42.7.x.
     *
     * TODO [MANUAL]: If Shopizer uses SSL connections to PostgreSQL, review
     *   SSL property changes introduced in 42.3.x:
     *   Old: ssl=true&sslfactory=org.postgresql.ssl.NonValidatingFactory
     *   New: sslmode=require (or verify-ca, verify-full)
     *   Reference: PostgreSQL JDBC 42.3.x — "SSL configuration changes"
     *
     * TODO [MANUAL]: Test all database connection pool configurations (HikariCP
     *   is the default in Spring Boot 3.x) with the new driver version.
     */
    public static class PostgresqlDriverMigrationNotes {
        // Documentation placeholder — no runtime shim required for driver upgrade.
        // The driver upgrade is a pom.xml version change only.
        // See TODO comments above for required validation steps.
    }

    // =========================================================================
    // SECTION 12: APPLICATION PROPERTIES / CONFIG FORMAT MIGRATION
    // =========================================================================

    /**
     * ConfigMigrationHelper transforms old Spring Boot 2.5.x application.properties
     * keys to their Spring Boot 3.3.x equivalents.
     *
     * BREAKING CHANGES in Spring Boot 3.x configuration:
     *   - spring.redis.* → spring.data.redis.*
     *   - spring.data.mongodb.* (largely unchanged but verify)
     *   - management.metrics.export.* → management.*.metrics.export.*
     *   - spring.security.oauth2.* paths changed
     *   - server.max-http-header-size → server.max-http-request-header-size
     *   - spring.mvc.pathmatch.use-suffix-pattern removed (was deprecated in 2.6)
     *   - spring.mvc.pathmatch.matching-strategy default changed to
     *     PATH_PATTERN_PARSER (was ANT_PATH_MATCHER in 2.5.x)
     *
     * TODO [MANUAL]: Run the Spring Boot 2.x → 3.x properties migrator tool or
     *   apply the OpenRewrite recipe:
     *   "org.openrewrite.java.spring.boot3.SpringBootProperties_3_0"
     *
     * TODO [MANUAL]: Verify Shopizer's application.properties / application.yml
     *   for all deprecated property keys listed below.
     *
     * TODO [MANUAL]: The default path matching strategy changed from
     *   AntPathMatcher to PathPatternParser in Spring Boot 3.x. If Shopizer
     *   uses suffix pattern matching (e.g., /api/products.json), this will break.
     *   Add spring.mvc.pathmatch.matching-strategy=ant_path_matcher only as a
     *   temporary workaround — migrate to PathPatternParser long-term.
     */
    public static class ConfigMigrationHelper {

        private static final Map<String, String> PROPERTY_RENAMES = new HashMap<>();

        static {
            // Spring Boot 3.x property renames
            // BREAKING CHANGE: spring.redis.* renamed to spring.data.redis.*
            PROPERTY_RENAMES.put("spring.redis.host", "spring.data.redis.host");
            PROPERTY_RENAMES.put("spring.redis.port", "spring.data.redis.port");
            PROPERTY_RENAMES.put("spring.redis.password", "spring.data.redis.password");
            PROPERTY_RENAMES.put("spring.redis.database", "spring.data.redis.database");
            PROPERTY_RENAMES.put("spring.redis.timeout", "spring.data.redis.timeout");
            PROPERTY_RENAMES.put("spring.redis.ssl", "spring.data.redis.ssl.enabled");
            PROPERTY_RENAMES.put("spring.redis.lettuce.pool.max-active",
                "spring.data.redis.lettuce.pool.max-active");
            PROPERTY_RENAMES.put("spring.redis.lettuce.pool.max-idle",
                "spring.data.redis.lettuce.pool.max-idle");

            // BREAKING CHANGE: server.max-http-header-size renamed
            PROPERTY_RENAMES.put("server.max-http-header-size",
                "server.max-http-request-header-size");

            // BREAKING CHANGE: management endpoint property prefix changes
            PROPERTY_RENAMES.put("management.metrics.export.prometheus.enabled",
                "management.prometheus.metrics.export.enabled");

            // BREAKING CHANGE: spring.mvc.pathmatch.use-suffix-pattern removed
            // No direct replacement — suffix pattern matching removed in Spring 6.x
            // TODO [MANUAL]: Remove spring.mvc.pathmatch.use-suffix-pattern=true if present.
            //   Suffix pattern matching is not supported in Spring Boot 3.x.

            // BREAKING CHANGE: Springfox properties replaced by springdoc properties
            PROPERTY_RENAMES.put("springfox.documentation.swagger-ui.enabled",
                "springdoc.swagger-ui.enabled");
            PROPERTY_RENAMES.put("springfox.documentation.enabled",
                "springdoc.api-docs.enabled");
        }

        /**
         * Migrates old Spring Boot 2.5.x properties to Spring Boot 3.3.x equivalents.
         *
         * @param oldProperties Properties loaded from the old application.properties
         * @return Migrated properties with renamed keys
         */
        public static Properties migrateProperties(Properties oldProperties) {
            Properties newProperties = new Properties();

            for (String key : oldProperties.stringPropertyNames()) {
                String value = oldProperties.getProperty(key);

                if (PROPERTY_RENAMES.containsKey(key)) {
                    String newKey = PROPERTY_RENAMES.get(key);
                    log.warn("CONFIG MIGRATION: Renaming property '{}' → '{}'", key, newKey);
                    newProperties.setProperty(newKey, value);
                } else if (key.startsWith("spring.redis.")) {
                    // Catch-all for any spring.redis.* properties not explicitly mapped
                    String newKey = key.replace("spring.redis.", "spring.data.redis.");
                    log.warn("CONFIG MIGRATION: Renaming property '{}' → '{}'", key, newKey);
                    newProperties.setProperty(newKey, value);
                } else if (key.equals("spring.mvc.pathmatch.use-suffix-pattern")) {
                    // TODO [MANUAL]: spring.mvc.pathmatch.use-suffix-pattern has been removed.
                    //   Suffix pattern matching is not supported in Spring Boot 3.x / Spring 6.x.
                    //   Remove this property and refactor any controllers relying on suffix matching.
                    log.error("CONFIG MIGRATION: Property '{}' has been REMOVED in Spring Boot 3.x. "
                        + "Manual intervention required — suffix pattern matching is not supported.", key);
                } else if (key.equals("spring.mvc.pathmatch.matching-strategy")
                        && "ant_path_matcher".equalsIgnoreCase(value)) {
                    // TODO [MANUAL]: AntPathMatcher is still supported in Spring Boot 3.x as a
                    //   fallback but PathPatternParser is the default and recommended strategy.
                    //   Migrate controllers to be compatible with PathPatternParser.
                    log.warn("CONFIG MIGRATION: '{}={}' — AntPathMatcher is supported but deprecated. "
                        + "Migrate to PathPatternParser (default in Spring Boot 3.x).", key, value);
                    newProperties.setProperty(key, value);
                } else {
                    newProperties.setProperty(key, value);
                }
            }

            return newProperties;
        }

        /**
         * Validates that no removed/unsupported properties remain after migration.
         *
         * TODO [MANUAL]: Run this validation as part of the CI/CD pipeline startup
         *   to catch any missed property migrations.
         */
        public static void validateNoRemovedProperties(Properties properties) {
            String[] removedProperties = {
                "spring.mvc.pathmatch.use-suffix-pattern",
                "springfox.documentation.swagger-ui.enabled",
                "springfox.documentation.enabled",
                "spring.redis.host",
                "spring.redis.port",
                "spring.redis.password",
                "server.max-http-header-size"
            };

            for (String removed : removedProperties) {
                if (properties.containsKey(removed)) {
                    log.error("CONFIG VALIDATION: Removed/renamed property '{}' still present. "
                        + "Manual migration required.", removed);
                }
            }
        }
    }

    // =========================================================================
    // SECTION 13: MAVEN POM.XML MIGRATION NOTES
    // =========================================================================

    /**
     * PomMigrationNotes documents required pom.xml changes for the upgrade.
     *
     * TODO [MANUAL]: Update spring-boot-starter-parent version:
     *   Old: <parent><artifactId>spring-boot-starter-parent</artifactId><version>2.5.12</version></parent>
     *   New: <parent><artifactId>spring-boot-starter-parent</artifactId><version>3.3.x</version></parent>
     *
     * TODO [MANUAL]: Java source/target version must be updated to 17 minimum.
     *   Spring Boot 3.x requires Java 17+.
     *   Old: <java.version>11</java.version>
     *   New: <java.version>17</java.version>
     *   Also update maven-compiler-plugin source/target to 17.
     *   NOTE: Runtime JVM must also be upgraded from JVM 11 to JVM 17+.
     *   Update Dockerfile base image and CI/CD (Jenkins, CircleCI) Java version.
     *
     * TODO [MANUAL]: Remove springfox-swagger2 and springfox-swagger-ui dependencies.
     *   Add: io.springdoc:springdoc-openapi-starter-webmvc-ui:2.x.x
     *
     * TODO [MANUAL]: Update jjwt dependencies:
     *   Remove: io.jsonwebtoken:jjwt:0.8.0
     *   Add:    io.jsonwebtoken:jjwt-api:0.12.x
     *           io.jsonwebtoken:jjwt-impl:0.12.x (runtime)
     *           io.jsonwebtoken:jjwt-jackson:0.12.x (runtime)
     *
     * TODO [MANUAL]: Update commons-fileupload:
     *   Old: commons-fileupload:commons-fileupload:1.3.3
     *   New: commons-fileupload:commons-fileupload:1.5 (or remove if using Spring's built-in)
     *
     * TODO [MANUAL]: Update postgresql driver:
     *   Old: org.postgresql:postgresql:42.2.18
     *   New: org.postgresql:postgresql:42.7.x
     *
     * TODO [MANUAL]: Update Drools BOM/dependencies to 9.x.
     *   Remove: kie-spring (no longer available in 9.x)
     *
     * TODO [MANUAL]: Update Infinispan BOM/dependencies to 15.x.
     *   Old starter: infinispan-spring-boot-starter-embedded
     *   New starter: infinispan-spring-boot-3-starter-embedded
     *
     * TODO [MANUAL]: Update MapStruct:
     *   Old: org.mapstruct:mapstruct:1.3.0.Final + org.mapstruct:mapstruct-processor:1.3.0.Final
     *   New: org.mapstruct:mapstruct:1.6.x + org.mapstruct:mapstruct-processor:1.6.x
     *
     * TODO [MANUAL]: Update maven-compiler-plugin annotationProcessorPaths to include
     *   mapstruct-processor 1.6.x (and lombok-mapstruct-binding if Lombok is used).
     *
     * TODO [MANUAL]: Update Dockerfile base image:
     *   Old: FROM eclipse-temurin:11-jre (or equivalent JVM 11 image)
     *   New: FROM eclipse-temurin:17-jre (minimum for Spring Boot 3.x)
     *
     * TODO [MANUAL]: Update Jenkins and CircleCI pipeline Java version to 17+.
     *   Jenkins: Update JDK tool configuration or agent Docker image.
     *   CircleCI: Update the docker image in .circleci/config.yml to use Java 17.
     *
     * TODO [MANUAL]: Update SonarCloud analysis to use Java 17 scanner.
     *   Verify sonar.java.source=17 in sonar-project.properties or pom.xml.
     */
    public static class PomMigrationNotes {
        // Documentation placeholder — see TODO comments above.
    }

    // =========================================================================
    // SECTION 14: CLOUD STORAGE INTEGRATION NOTES (AWS S3, Azure, GCP)
    // =========================================================================

    /**
     * CloudStorageMigrationNotes documents potential breaking changes in cloud
     * storage integrations detected in the Shopizer codebase.
     *
     * Technologies detected: aws s3, azure sdk for java, gcp storage
     *
     * TODO [MANUAL]: Verify AWS SDK version compatibility with Spring Boot 3.x.
     *   If using AWS SDK v1 (com.amazonaws.*), consider migrating to AWS SDK v2
     *   (software.amazon.awssdk.*) which is the recommended version for Spring Boot 3.x.
     *   Spring Cloud AWS 3.x (for Spring Boot 3.x) requires AWS SDK v2.
     *
     * TODO [MANUAL]: Verify Azure SDK for Java version compatibility.
     *   Spring Boot 3.x requires Azure Spring Boot Starter 5.x (for Spring Boot 3.x).
     *   Old: com.azure.spring:azure-spring-boot-starter:3.x (for Spring Boot 2.x)
     *   New: com.azure.spring:spring-cloud-azure-starter:5.x (for Spring Boot 3.x)
     *
     * TODO [MANUAL]: Verify GCP Storage SDK version compatibility with Spring Boot 3.x.
     *   Spring Cloud GCP 4.x supports Spring Boot 3.x.
     *   Old: com.google.cloud:spring-cloud-gcp-starter-storage:3.x
     *   New: com.google.cloud:spring-cloud-gcp-starter-storage:4.x+
     */
    public static class CloudStorageMigrationNotes {
        // Documentation placeholder — see TODO comments above.
    }

    // =========================================================================
    // SECTION 15: JPA ENTITY MIGRATION NOTES (50 entities in sm-core-model)
    // =========================================================================

    /**
     * JpaEntityMigrationNotes documents required changes for the 50 JPA entities
     * in sm-core-model after the javax.* → jakarta.* namespace migration.
     *
     * TODO [MANUAL]: All 50 JPA entities in sm-core-model must have their
     *   javax.persistence.* imports replaced with jakarta.persistence.*.
     *   Use OpenRewrite or IDE bulk refactoring for this change.
     *
     * TODO [MANUAL]: Hibernate 6.x (bundled with Spring Boot 3.x) has breaking changes:
     *   - @Type(type = "...") string-based type names removed — use @Type(value = ...)
     *     with the actual UserType class reference.
     *   - Custom UserType implementations must implement the new Hibernate 6.x
     *     UserType<T> generic interface.
     *   - @TypeDef / @TypeDefs annotations removed — use @Type directly on fields.
     *   - ImplicitNamingStrategy and PhysicalNamingStrategy API changes.
     *   Reference: Hibernate 6.x migration guide
     *
     * TODO [MANUAL]: Verify all @Column(columnDefinition = "...") annotations
     *   use database-portable type names compatible with the PostgreSQL driver 42.7.x.
     *
     * TODO [MANUAL]: Review all @OneToMany, @ManyToMany fetch type configurations.
     *   Hibernate 6.x is stricter about lazy loading outside of transactions.
     *
     * TODO [MANUAL]: If Shopizer uses Hibernate's legacy id generator strategies
     *   (e.g., @GeneratedValue(strategy = GenerationType.AUTO) with Hibernate's
     *   SequenceStyleGenerator), verify behavior in Hibernate 6.x — the default
     *   id generation strategy changed.
     *   Reference: Hibernate 6.x — "Default id generation strategy change"
     */
    public static class JpaEntityMigrationNotes {
        // Documentation placeholder — see TODO comments above.
    }

    // =========================================================================
    // SECTION 16: BEAN WIRING VALIDATION (150 Spring Beans)
    // =========================================================================

    /**
     * SpringBeanMigrationNotes documents potential Spring Bean wiring issues
     * after the Spring Boot 3.x upgrade across the 150 Spring Beans detected.
     *
     * TODO [MANUAL]: Spring Boot 3.x removed support for the legacy
     *   spring.factories auto-configuration mechanism in favor of
     *   META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports.
     *   If any Shopizer module uses spring.factories for auto-configuration,
     *   migrate to the new imports file format.
     *   Reference: Spring Boot 3.0 — "Auto-configuration registration"
     *
     * TODO [MANUAL]: @Autowired field injection on non-Spring-managed classes
     *   will fail silently in Spring Boot 3.x. Verify all 150 beans use
     *   constructor injection or are properly managed by the Spring context.
     *
     * TODO [MANUAL]: Spring Boot 3.x circular dependency detection is stricter.
     *   Run the application and address any circular dependency errors.
     *   Use spring.main.allow-circular-references=true only as a temporary workaround.
     *
     * TODO [MANUAL]: Verify all @Configuration classes in the multi-module Maven
     *   project are correctly scanned. Spring Boot 3.x component scanning behavior
     *   with multi-module projects may require explicit @ComponentScan configuration.
     */
    public static class SpringBeanMigrationNotes {
        // Documentation placeholder — see TODO comments above.
    }

    // =========================================================================
    // SECTION 17: BEAN PROVIDING JwtTokenProviderShim
    // =========================================================================

    /**
     * TODO [MANUAL]: Replace the placeholder secret and expiration values below
     *   with Shopizer's actual JWT configuration from application.properties.
     *   Typical property names: jwt.secret, jwt.expiration (or similar).
     *   Ensure the secret is at least 32 characters for HS256.
     */
    @Bean
    public JwtTokenProviderShim jwtTokenProviderShim(
            @Value("${jwt.secret:REPLACE_WITH_SECURE_SECRET_MIN_32_CHARS_LONG}") String secret,
            @Value("${jwt.expiration:86400000}") long expirationMs) {
        // TODO [MANUAL]: Verify property names match Shopizer's actual application.properties keys.
        return new JwtTokenProviderShim(secret, expirationMs);
    }

    @Bean
    public DroolsSessionShim droolsSessionShim(KieContainer kieContainer) {
        return new DroolsSessionShim(kieContainer);
    }

    @Bean
    public InfinispanCacheShim infinispanCacheShim(EmbeddedCacheManager cacheManager) {
        return new InfinispanCacheShim(cacheManager);
    }
}