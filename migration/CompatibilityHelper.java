package com.migration.shim;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.HashMap;
import java.util.Map;

/**
 * Spring Boot 2.5.12 → 3.3.x Migration Compatibility Shim
 *
 * Addresses breaking changes across:
 *  - javax → jakarta namespace migration
 *  - Spring Security 5.5.x → 6.3.x
 *  - Spring MVC 5.3.x → 6.1.x
 *  - Springfox Swagger2 2.9.2 → springdoc-openapi 2.x
 *  - Hibernate 5.4.x → 6.5.x
 *  - JJWT 0.8.0 → 0.12.x
 *  - Infinispan 9.4.18.Final → 15.x
 *  - MapStruct 1.3.0.Final → 1.6.x
 *  - commons-fileupload 1.3.3 → 1.5+
 *
 * Usage: Reference this shim during migration to identify and resolve breaking changes.
 * Each section documents the old API, the new API, and provides bridge utilities where possible.
 */
public class SpringBootMigrationShim {

    private static final Logger log = LoggerFactory.getLogger(SpringBootMigrationShim.class);

    // =========================================================================
    // SECTION 1: javax → jakarta Namespace Migration
    // Spring Boot 3.x requires Jakarta EE 9+ (jakarta.*) instead of javax.*
    // =========================================================================

    /**
     * javax → jakarta package rename reference map.
     * All source files importing javax.* EE packages must be updated to jakarta.*
     *
     * TODO: Run a global find-and-replace across all source files for each mapping below.
     *       Breaking change: Spring Boot 3.x dropped all javax.* EE support in favour of jakarta.*
     *       See: https://spring.io/blog/2022/05/24/preparing-for-spring-6
     */
    public static final Map<String, String> JAVAX_TO_JAKARTA_PACKAGE_MAP = new HashMap<>() {{
        // Servlet API
        put("javax.servlet.", "jakarta.servlet.");
        put("javax.servlet.http.", "jakarta.servlet.http.");
        put("javax.servlet.annotation.", "jakarta.servlet.annotation.");
        put("javax.servlet.descriptor.", "jakarta.servlet.descriptor.");

        // Persistence / JPA
        put("javax.persistence.", "jakarta.persistence.");
        put("javax.transaction.", "jakarta.transaction.");

        // Validation
        put("javax.validation.", "jakarta.validation.");
        put("javax.validation.constraints.", "jakarta.validation.constraints.");

        // XML Binding
        put("javax.xml.bind.", "jakarta.xml.bind.");
        put("javax.xml.bind.annotation.", "jakarta.xml.bind.annotation.");

        // Annotation
        put("javax.annotation.", "jakarta.annotation.");

        // Mail
        put("javax.mail.", "jakarta.mail.");

        // WebSocket
        put("javax.websocket.", "jakarta.websocket.");

        // Inject
        put("javax.inject.", "jakarta.inject.");

        // EL
        put("javax.el.", "jakarta.el.");
    }};

    /**
     * Utility: logs all javax→jakarta replacements that must be applied manually.
     *
     * TODO: Replace all javax.* imports in every .java file in the project.
     *       This cannot be automated safely without AST tooling — use OpenRewrite recipe
     *       "org.openrewrite.java.migrate.jakarta.JavaxMigrationToJakarta" for bulk migration.
     */
    public static void printJavaxToJakartaMigrationGuide() {
        log.warn("=== javax → jakarta Migration Required ===");
        JAVAX_TO_JAKARTA_PACKAGE_MAP.forEach((oldPkg, newPkg) ->
            log.warn("  Replace: {} → {}", oldPkg, newPkg));
        log.warn("===========================================");
    }

    // =========================================================================
    // SECTION 2: Spring Security 5.5.x → 6.3.x Breaking Changes
    // =========================================================================

    /**
     * Spring Security 6.x removed WebSecurityConfigurerAdapter.
     * All security configuration must extend SecurityFilterChain beans instead.
     *
     * OLD (Spring Security 5.x):
     * <pre>
     *   {@code @Configuration}
     *   public class SecurityConfig extends WebSecurityConfigurerAdapter {
     *       {@code @Override}
     *       protected void configure(HttpSecurity http) throws Exception { ... }
     *   }
     * </pre>
     *
     * NEW (Spring Security 6.x):
     * <pre>
     *   {@code @Configuration}
     *   public class SecurityConfig {
     *       {@code @Bean}
     *       public SecurityFilterChain filterChain(HttpSecurity http) throws Exception { ... }
     *   }
     * </pre>
     *
     * TODO: Remove all classes extending WebSecurityConfigurerAdapter.
     *       Breaking change: WebSecurityConfigurerAdapter was removed in Spring Security 6.0.
     *       Migrate to SecurityFilterChain @Bean pattern.
     */
    public static void securityConfigurerAdapterMigrationGuide() {
        log.warn("WebSecurityConfigurerAdapter has been removed in Spring Security 6.x.");
        log.warn("Migrate to @Bean SecurityFilterChain pattern.");
    }

    /**
     * Spring Security 6.x: antMatchers() / mvcMatchers() / regexMatchers() removed.
     * Use requestMatchers() instead.
     *
     * OLD: http.authorizeRequests().antMatchers("/api/**").authenticated()
     * NEW: http.authorizeHttpRequests().requestMatchers("/api/**").authenticated()
     *
     * TODO: Replace all antMatchers(), mvcMatchers(), regexMatchers() calls with requestMatchers().
     *       Breaking change: These methods were removed in Spring Security 6.0.
     *       Also replace authorizeRequests() with authorizeHttpRequests().
     */
    public static void requestMatcherMigrationGuide() {
        log.warn("antMatchers/mvcMatchers/regexMatchers removed. Use requestMatchers().");
        log.warn("authorizeRequests() removed. Use authorizeHttpRequests().");
    }

    /**
     * Spring Security 6.x: SecurityContextHolder strategy changes.
     * HttpSessionSecurityContextRepository.SPRING_SECURITY_CONTEXT_KEY is still valid,
     * but SecurityContextPersistenceFilter is replaced by SecurityContextHolderFilter.
     *
     * TODO: If SecurityContextPersistenceFilter is referenced directly, replace with
     *       SecurityContextHolderFilter. Breaking change in Spring Security 6.0.
     */
    public static Authentication getCurrentAuthentication() {
        // Compatible with Spring Security 6.x
        return SecurityContextHolder.getContext().getAuthentication();
    }

    /**
     * Spring Security 6.x: UserDetailsService.loadUserByUsername() contract unchanged,
     * but PasswordEncoder beans must be explicitly declared — no default encoding.
     *
     * TODO: Ensure a PasswordEncoder @Bean is declared in your security configuration.
     *       Spring Security 6.x does not provide a default PasswordEncoder.
     *       Recommended: BCryptPasswordEncoder or DelegatingPasswordEncoder.
     */
    public static void passwordEncoderMigrationGuide() {
        log.warn("Ensure PasswordEncoder @Bean is explicitly declared for Spring Security 6.x.");
    }

    /**
     * Spring Security 6.x: CSRF protection defaults changed.
     * CookieCsrfTokenRepository.withHttpOnlyFalse() behaviour changed — must use
     * XorCsrfTokenRequestAttributeHandler for SPA/REST APIs.
     *
     * TODO: Review CSRF configuration. If using stateless REST APIs, explicitly disable CSRF
     *       or configure XorCsrfTokenRequestAttributeHandler.
     *       Breaking change: CsrfTokenRequestAttributeHandler is now the default.
     */
    public static void csrfMigrationGuide() {
        log.warn("CSRF token handling changed in Spring Security 6.x.");
        log.warn("For REST APIs: http.csrf(csrf -> csrf.disable())");
        log.warn("For SPAs: use XorCsrfTokenRequestAttributeHandler.");
    }

    // =========================================================================
    // SECTION 3: Spring MVC 5.3.x → 6.1.x Breaking Changes
    // =========================================================================

    /**
     * Spring MVC 6.x: PathMatchConfigurer.setUseTrailingSlashMatch() removed.
     * Trailing slash matching is no longer supported by default.
     *
     * OLD: configurer.setUseTrailingSlashMatch(true)
     * NEW: Not supported — update client URLs or add explicit mappings.
     *
     * TODO: Remove setUseTrailingSlashMatch() calls from WebMvcConfigurer implementations.
     *       Breaking change: Trailing slash matching removed in Spring MVC 6.0.
     *       Add explicit @RequestMapping entries with and without trailing slash if needed.
     */
    public static void trailingSlashMigrationGuide() {
        log.warn("setUseTrailingSlashMatch() removed in Spring MVC 6.x.");
        log.warn("Add explicit @RequestMapping variants or update client URLs.");
    }

    /**
     * Spring MVC 6.x: HttpMethod is now an enum-like final class, not an enum.
     * HttpMethod.resolve(String) replaced by HttpMethod.valueOf(String).
     *
     * OLD: HttpMethod.resolve("GET")
     * NEW: HttpMethod.valueOf("GET")
     *
     * TODO: Replace HttpMethod.resolve() calls with HttpMethod.valueOf().
     *       Breaking change: HttpMethod.resolve() removed in Spring MVC 6.0.
     */
    public static org.springframework.http.HttpMethod resolveHttpMethod(String method) {
        // TODO: Callers previously using HttpMethod.resolve() should use HttpMethod.valueOf()
        return org.springframework.http.HttpMethod.valueOf(method.toUpperCase());
    }

    /**
     * Spring MVC 6.x: MockMvc and test infrastructure moved to spring-test 6.x.
     * MockHttpServletRequest/Response now use jakarta.servlet.* internally.
     *
     * TODO: Update all test imports from javax.servlet.* to jakarta.servlet.*
     *       in MockMvc-based integration tests.
     */
    public static void mockMvcTestMigrationGuide() {
        log.warn("MockMvc tests require jakarta.servlet.* imports in Spring MVC 6.x.");
    }

    // =========================================================================
    // SECTION 4: Springfox Swagger2 2.9.2 → springdoc-openapi 2.x Migration
    // =========================================================================

    /**
     * Springfox Swagger2 is abandoned and incompatible with Spring Boot 3.x.
     * Replace with springdoc-openapi-starter-webmvc-ui 2.5.0.
     *
     * OLD Maven dependency:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.springfox&lt;/groupId&gt;
     *     &lt;artifactId&gt;springfox-swagger2&lt;/artifactId&gt;
     *     &lt;version&gt;2.9.2&lt;/version&gt;
     *   &lt;/dependency&gt;
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.springfox&lt;/groupId&gt;
     *     &lt;artifactId&gt;springfox-swagger-ui&lt;/artifactId&gt;
     *     &lt;version&gt;2.9.2&lt;/version&gt;
     *   &lt;/dependency&gt;
     * </pre>
     *
     * NEW Maven dependency:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;org.springdoc&lt;/groupId&gt;
     *     &lt;artifactId&gt;springdoc-openapi-starter-webmvc-ui&lt;/artifactId&gt;
     *     &lt;version&gt;2.5.0&lt;/version&gt;
     *   &lt;/dependency&gt;
     * </pre>
     *
     * TODO: Remove all springfox-swagger2 and springfox-swagger-ui dependencies from pom.xml.
     *       Add springdoc-openapi-starter-webmvc-ui 2.5.0.
     *       Breaking change: Springfox is incompatible with Spring Boot 3.x / Spring MVC 6.x.
     */
    public static void swaggerMigrationGuide() {
        log.warn("Springfox Swagger2 must be replaced with springdoc-openapi-starter-webmvc-ui 2.5.0.");
    }

    /**
     * Springfox annotation → springdoc annotation mapping.
     *
     * OLD Springfox → NEW springdoc-openapi (io.swagger.v3.oas.annotations):
     *
     * @Api(tags="...")                    → @Tag(name="...")
     * @ApiOperation(value="...")          → @Operation(summary="...")
     * @ApiParam(value="...")              → @Parameter(description="...")
     * @ApiModel(description="...")        → @Schema(description="...")
     * @ApiModelProperty(value="...")      → @Schema(description="...")
     * @ApiResponse(code=200, message="") → @ApiResponse(responseCode="200", description="")
     * @ApiIgnore                          → @Parameter(hidden=true) or @Operation(hidden=true)
     * @EnableSwagger2                     → Remove (springdoc auto-configures)
     * Docket @Bean                        → Remove (springdoc auto-configures via application.properties)
     *
     * TODO: Replace all Springfox annotations with springdoc-openapi equivalents listed above.
     *       Breaking change: io.swagger.annotations.* (Swagger 2) replaced by
     *       io.swagger.v3.oas.annotations.* (OpenAPI 3) in springdoc-openapi 2.x.
     */
    public static final Map<String, String> SPRINGFOX_TO_SPRINGDOC_ANNOTATION_MAP = new HashMap<>() {{
        put("@Api", "@Tag");
        put("@ApiOperation", "@Operation");
        put("@ApiParam", "@Parameter");
        put("@ApiModel", "@Schema");
        put("@ApiModelProperty", "@Schema");
        put("@ApiResponse", "@ApiResponse (responseCode as String)");
        put("@ApiIgnore", "@Parameter(hidden=true) or @Operation(hidden=true)");
        put("@EnableSwagger2", "REMOVE — springdoc auto-configures");
        put("Docket @Bean", "REMOVE — configure via springdoc.* properties");
    }};

    /**
     * springdoc-openapi 2.x application.properties configuration shim.
     *
     * TODO: Add the following to application.properties / application.yml:
     *
     *   springdoc.api-docs.path=/v3/api-docs
     *   springdoc.swagger-ui.path=/swagger-ui.html
     *   springdoc.swagger-ui.enabled=true
     *   springdoc.packages-to-scan=com.yourcompany.api
     *
     * Old Springfox Docket configuration (title, description, version, contact) must be
     * migrated to an OpenAPI @Bean:
     *
     * <pre>
     *   {@code @Bean}
     *   public OpenAPI customOpenAPI() {
     *       return new OpenAPI()
     *           .info(new Info()
     *               .title("Your API Title")
     *               .version("1.0")
     *               .description("Your API Description"));
     *   }
     * </pre>
     *
     * Breaking change: Docket bean is not recognised by springdoc-openapi.
     */
    public static void springdocConfigMigrationGuide() {
        log.warn("Migrate Springfox Docket @Bean to springdoc OpenAPI @Bean.");
        log.warn("Add springdoc.* properties to application.properties.");
    }

    // =========================================================================
    // SECTION 5: Hibernate 5.4.x → 6.5.x Breaking Changes
    // =========================================================================

    /**
     * Hibernate 6.x: javax.persistence.* → jakarta.persistence.*
     * All JPA annotations and APIs must use jakarta.persistence.* package.
     *
     * TODO: Replace all javax.persistence.* imports with jakarta.persistence.*
     *       Breaking change: Hibernate 6.x dropped javax.persistence support entirely.
     */
    public static void hibernateJakartaMigrationGuide() {
        log.warn("Hibernate 6.x requires jakarta.persistence.* — replace all javax.persistence.* imports.");
    }

    /**
     * Hibernate 6.x: Implicit naming strategy changes.
     * The default ImplicitNamingStrategy changed — table/column names may differ.
     *
     * TODO: If relying on Hibernate's implicit naming, verify generated DDL matches existing schema.
     *       Set spring.jpa.hibernate.naming.implicit-strategy explicitly if needed:
     *       spring.jpa.hibernate.naming.implicit-strategy=
     *           org.hibernate.boot.model.naming.ImplicitNamingStrategyLegacyJpaImpl
     *       Breaking change: Default naming strategy changed in Hibernate 6.0.
     */
    public static void hibernateNamingStrategyMigrationGuide() {
        log.warn("Hibernate 6.x changed default ImplicitNamingStrategy — verify schema DDL.");
    }

    /**
     * Hibernate 6.x: Criteria API changes.
     * CriteriaQuery and related APIs now use jakarta.persistence.criteria.* package.
     * Some deprecated Hibernate-specific Criteria API (org.hibernate.Criteria) was removed.
     *
     * TODO: Replace org.hibernate.Criteria usage with jakarta.persistence.criteria.CriteriaQuery.
     *       Breaking change: Legacy Hibernate Criteria API removed in Hibernate 6.0.
     */
    public static void hibernateCriteriaMigrationGuide() {
        log.warn("Legacy org.hibernate.Criteria removed. Use jakarta.persistence.criteria.CriteriaQuery.");
    }

    /**
     * Hibernate 6.x: @Type annotation changes.
     * org.hibernate.annotations.Type(type="...") string-based type names replaced by
     * @Type(value=SomeUserType.class) class-based references.
     *
     * TODO: Update all @Type annotations to use class references instead of string type names.
     *       Breaking change: String-based @Type(type="...") removed in Hibernate 6.0.
     */
    public static void hibernateTypeMigrationGuide() {
        log.warn("@Type(type=\"...\") string names removed. Use @Type(value=YourType.class).");
    }

    /**
     * Hibernate 6.x: hbm.xml mapping files.
     * Legacy hbm.xml format support is deprecated and may require migration to annotations.
     *
     * TODO: Migrate any remaining hbm.xml mapping files to JPA annotations or orm.xml.
     *       Breaking change: hbm.xml support deprecated in Hibernate 6.x.
     */
    public static void hibernateHbmXmlMigrationGuide() {
        log.warn("hbm.xml mapping files deprecated in Hibernate 6.x. Migrate to JPA annotations.");
    }

    // =========================================================================
    // SECTION 6: JJWT 0.8.0 → 0.12.x Migration
    // =========================================================================

    /**
     * JJWT 0.12.x introduced a completely redesigned fluent API.
     * The old Jwts.parser() and Jwts.builder() APIs changed significantly.
     *
     * OLD (JJWT 0.8.0):
     * <pre>
     *   String token = Jwts.builder()
     *       .setSubject("user")
     *       .signWith(SignatureAlgorithm.HS512, secret)
     *       .compact();
     *
     *   Claims claims = Jwts.parser()
     *       .setSigningKey(secret)
     *       .parseClaimsJws(token)
     *       .getBody();
     * </pre>
     *
     * NEW (JJWT 0.12.x):
     * <pre>
     *   SecretKey key = Keys.hmacShaKeyFor(Decoders.BASE64.decode(secret));
     *
     *   String token = Jwts.builder()
     *       .subject("user")
     *       .signWith(key)
     *       .compact();
     *
     *   Claims claims = Jwts.parserBuilder()
     *       .verifyWith(key)
     *       .build()
     *       .parseSignedClaims(token)
     *       .getPayload();
     * </pre>
     *
     * TODO: Replace all JJWT 0.8.0 API calls with JJWT 0.12.x equivalents.
     *       Breaking change: Jwts.parser() replaced by Jwts.parserBuilder().build().
     *       Breaking change: signWith(SignatureAlgorithm, String) replaced by signWith(SecretKey).
     *       Breaking change: parseClaimsJws() replaced by parseSignedClaims().
     *       Breaking change: getBody() replaced by getPayload().
     *       CVE remediation: JJWT 0.8.0 has known JWT parsing vulnerabilities.
     *
     * Maven dependency change:
     * OLD:
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.jsonwebtoken&lt;/groupId&gt;
     *     &lt;artifactId&gt;jjwt&lt;/artifactId&gt;
     *     &lt;version&gt;0.8.0&lt;/version&gt;
     *   &lt;/dependency&gt;
     *
     * NEW:
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.jsonwebtoken&lt;/groupId&gt;
     *     &lt;artifactId&gt;jjwt-api&lt;/artifactId&gt;
     *     &lt;version&gt;0.12.6&lt;/version&gt;
     *   &lt;/dependency&gt;
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.jsonwebtoken&lt;/groupId&gt;
     *     &lt;artifactId&gt;jjwt-impl&lt;/artifactId&gt;
     *     &lt;version&gt;0.12.6&lt;/version&gt;
     *     &lt;scope&gt;runtime&lt;/scope&gt;
     *   &lt;/dependency&gt;
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;io.jsonwebtoken&lt;/groupId&gt;
     *     &lt;artifactId&gt;jjwt-jackson&lt;/artifactId&gt;
     *     &lt;version&gt;0.12.6&lt;/version&gt;
     *     &lt;scope&gt;runtime&lt;/scope&gt;
     *   &lt;/dependency&gt;
     */
    public static void jjwtMigrationGuide() {
        log.warn("JJWT 0.8.0 → 0.12.6 migration required. API completely redesigned.");
        log.warn("Replace jjwt artifact with jjwt-api + jjwt-impl + jjwt-jackson.");
        log.warn("Replace Jwts.parser() with Jwts.parserBuilder().verifyWith(key).build().");
        log.warn("Replace parseClaimsJws() with parseSignedClaims().");
        log.warn("Replace getBody() with getPayload().");
    }

    /**
     * JJWT API method rename reference map for automated search-and-replace guidance.
     *
     * TODO: Apply these replacements to all JWT utility/service classes.
     */
    public static final Map<String, String> JJWT_API_RENAME_MAP = new HashMap<>() {{
        put("Jwts.parser()", "Jwts.parserBuilder().verifyWith(key).build()");
        put(".setSigningKey(", ".verifyWith(");
        put(".parseClaimsJws(", ".parseSignedClaims(");
        put(".getBody()", ".getPayload()");
        put("signWith(SignatureAlgorithm.HS256,", "signWith(key) // use Keys.hmacShaKeyFor()");
        put("signWith(SignatureAlgorithm.HS384,", "signWith(key) // use Keys.hmacShaKeyFor()");
        put("signWith(SignatureAlgorithm.HS512,", "signWith(key) // use Keys.hmacShaKeyFor()");
        put(".setSubject(", ".subject(");
        put(".setIssuedAt(", ".issuedAt(");
        put(".setExpiration(", ".expiration(");
        put(".setIssuer(", ".issuer(");
        put(".setAudience(", ".audience().add(");
        put(".setClaims(", ".claims(");
    }};

    // =========================================================================
    // SECTION 7: Infinispan 9.4.18.Final → 15.x Migration
    // =========================================================================

    /**
     * Infinispan 9.x → 15.x: Major API and configuration changes.
     * Alternatively, migrate to Spring Cache with Redis for cloud-native scaling.
     *
     * TODO: Evaluate whether to upgrade Infinispan to 15.x or migrate to Spring Cache + Redis.
     *       Breaking change: Infinispan 15.x requires significant configuration migration.
     *       Recommended path for cloud-native: Replace Infinispan with spring-boot-starter-data-redis
     *       and @EnableCaching with RedisCacheManager.
     */
    public static void infinispanMigrationGuide() {
        log.warn("Infinispan 9.4.18.Final → 15.x requires major configuration migration.");
        log.warn("Consider migrating to Spring Cache + Redis for cloud-native horizontal scaling.");
    }

    /**
     * Infinispan 15.x: Configuration XML schema changed.
     * infinispan.xml configuration format updated — old format not compatible.
     *
     * OLD infinispan.xml root element:
     *   &lt;infinispan xmlns="urn:infinispan:config:9.4"&gt;
     *
     * NEW infinispan.xml root element:
     *   &lt;infinispan xmlns="urn:infinispan:config:15.0"&gt;
     *
     * TODO: Update infinispan.xml schema namespace from 9.4 to 15.0.
     *       Review all cache configuration elements for removed/renamed attributes.
     *       Breaking change: Configuration schema version must match Infinispan runtime version.
     */
    public static String migrateInfinispanConfigNamespace(String oldConfig) {
        if (oldConfig == null) return null;
        // TODO: This is a simple namespace replacement — full config migration requires manual review
        //       of eviction, expiration, clustering, and persistence configuration sections.
        String migrated = oldConfig.replace(
            "urn:infinispan:config:9.4",
            "urn:infinispan:config:15.0"
        );
        log.warn("Infinispan config namespace updated. Manual review of all cache config sections required.");
        return migrated;
    }

    /**
     * Infinispan 15.x: EmbeddedCacheManager API changes.
     * org.infinispan.manager.DefaultCacheManager constructor signatures changed.
     * GlobalConfiguration builder API updated.
     *
     * TODO: Review all DefaultCacheManager instantiation and GlobalConfigurationBuilder usage.
     *       Breaking change: Several GlobalConfiguration options renamed/removed in Infinispan 15.x.
     */
    public static void infinispanCacheManagerMigrationGuide() {
        log.warn("Review DefaultCacheManager and GlobalConfigurationBuilder usage for Infinispan 15.x.");
    }

    /**
     * Spring Cache + Redis migration alternative.
     *
     * If migrating from Infinispan to Spring Cache + Redis, add to pom.xml:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;org.springframework.boot&lt;/groupId&gt;
     *     &lt;artifactId&gt;spring-boot-starter-data-redis&lt;/artifactId&gt;
     *   &lt;/dependency&gt;
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;org.springframework.boot&lt;/groupId&gt;
     *     &lt;artifactId&gt;spring-boot-starter-cache&lt;/artifactId&gt;
     *   &lt;/dependency&gt;
     * </pre>
     *
     * And configure:
     *   spring.cache.type=redis
     *   spring.data.redis.host=localhost
     *   spring.data.redis.port=6379
     *
     * TODO: Replace @Infinispan-specific cache annotations/configuration with standard
     *       Spring @Cacheable, @CacheEvict, @CachePut annotations backed by RedisCacheManager.
     */
    public static void redisCacheMigrationGuide() {
        log.warn("Spring Cache + Redis migration: add spring-boot-starter-data-redis dependency.");
        log.warn("Configure spring.cache.type=redis and spring.data.redis.* properties.");
    }

    // =========================================================================
    // SECTION 8: MapStruct 1.3.0.Final → 1.6.x Migration
    // =========================================================================

    /**
     * MapStruct 1.6.x: Annotation processor version must match runtime version.
     *
     * TODO: Update both mapstruct and mapstruct-processor to 1.6.2 in pom.xml:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;org.mapstruct&lt;/groupId&gt;
     *     &lt;artifactId&gt;mapstruct&lt;/artifactId&gt;
     *     &lt;version&gt;1.6.2&lt;/version&gt;
     *   &lt;/dependency&gt;
     *   &lt;!-- In maven-compiler-plugin annotationProcessorPaths: --&gt;
     *   &lt;path&gt;
     *     &lt;groupId&gt;org.mapstruct&lt;/groupId&gt;
     *     &lt;artifactId&gt;mapstruct-processor&lt;/artifactId&gt;
     *     &lt;version&gt;1.6.2&lt;/version&gt;
     *   &lt;/path&gt;
     * </pre>
     */
    public static void mapStructMigrationGuide() {
        log.warn("Update mapstruct and mapstruct-processor to 1.6.2.");
    }

    /**
     * MapStruct 1.6.x: @Mapper componentModel default changed behaviour with Spring.
     * Ensure componentModel = "spring" is set on all @Mapper interfaces used with Spring DI.
     *
     * TODO: Verify all @Mapper interfaces have componentModel = "spring" if injected via Spring.
     *       Breaking change: Default componentModel behaviour may differ in 1.6.x with Spring Boot 3.x.
     */
    public static void mapStructSpringComponentModelGuide() {
        log.warn("Verify @Mapper(componentModel = \"spring\") on all Spring-injected MapStruct mappers.");
    }

    /**
     * MapStruct 1.6.x: Lombok compatibility.
     * If Lombok is used alongside MapStruct, ensure Lombok annotation processor runs before MapStruct.
     *
     * TODO: In maven-compiler-plugin annotationProcessorPaths, list lombok before mapstruct-processor.
     *       Breaking change: Order of annotation processors matters in MapStruct 1.6.x with Lombok.
     */
    public static void mapStructLombokOrderGuide() {
        log.warn("Ensure Lombok annotation processor is listed before mapstruct-processor in pom.xml.");
    }

    // =========================================================================
    // SECTION 9: commons-fileupload 1.3.3 → 1.5+ Migration
    // =========================================================================

    /**
     * commons-fileupload 1.3.3 is vulnerable to CVE-2023-24998 (DoS via excessive parts).
     * Upgrade to commons-fileupload 1.5+.
     *
     * TODO: Update commons-fileupload to 1.5+ in pom.xml:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;commons-fileupload&lt;/groupId&gt;
     *     &lt;artifactId&gt;commons-fileupload&lt;/artifactId&gt;
     *     &lt;version&gt;1.5&lt;/version&gt;
     *   &lt;/dependency&gt;
     * </pre>
     *
     * Breaking change: FileUpload 1.5 introduces FileCountMax limit (default 1000).
     * If your application accepts multipart requests with many parts, configure explicitly:
     *   DiskFileItemFactory factory = new DiskFileItemFactory();
     *   ServletFileUpload upload = new ServletFileUpload(factory);
     *   upload.setFileCountMax(100); // set appropriate limit
     *
     * TODO: Review all ServletFileUpload usages and set appropriate fileCountMax limits.
     *       CVE remediation: CVE-2023-24998 DoS via unbounded multipart part count.
     */
    public static void commonsFileUploadMigrationGuide() {
        log.warn("Upgrade commons-fileupload to 1.5+ for CVE-2023-24998 remediation.");
        log.warn("Set fileCountMax on all ServletFileUpload instances.");
    }

    // =========================================================================
    // SECTION 10: Spring Boot 3.3.x Application Properties Changes
    // =========================================================================

    /**
     * Spring Boot 3.x: application.properties key renames and removals.
     *
     * TODO: Apply the following property key migrations in application.properties / application.yml.
     *       Breaking change: Many spring.* property keys renamed in Spring Boot 3.x.
     */
    public static final Map<String, String> APPLICATION_PROPERTIES_RENAME_MAP = new HashMap<>() {{
        // Spring Data
        put("spring.data.elasticsearch.cluster-name", "REMOVED — use spring.elasticsearch.* properties");
        put("spring.data.elasticsearch.cluster-nodes", "REMOVED — use spring.elasticsearch.uris");
        put("spring.elasticsearch.rest.uris", "spring.elasticsearch.uris");
        put("spring.elasticsearch.rest.username", "spring.elasticsearch.username");
        put("spring.elasticsearch.rest.password", "spring.elasticsearch.password");

        // Spring MVC
        put("spring.mvc.pathmatch.use-suffix-pattern", "REMOVED — suffix pattern matching removed");
        put("spring.mvc.pathmatch.use-registered-suffix-pattern", "REMOVED");

        // Spring Security
        put("spring.security.oauth2.resourceserver.jwt.jwk-set-uri",
            "spring.security.oauth2.resourceserver.jwt.jwk-set-uri (unchanged)");

        // Actuator
        put("management.server.servlet.context-path", "management.server.base-path");

        // JPA / Hibernate
        put("spring.jpa.properties.hibernate.dialect",
            "spring.jpa.properties.hibernate.dialect (verify dialect class for Hibernate 6.x)");

        // Logging
        put("logging.file", "logging.file.name");
        put("logging.path", "logging.file.path");

        // Multipart
        put("spring.servlet.multipart.max-file-size", "spring.servlet.multipart.max-file-size (unchanged)");
        put("spring.servlet.multipart.max-request-size", "spring.servlet.multipart.max-request-size (unchanged)");
    }};

    /**
     * Transforms a subset of known renamed application.properties keys.
     * This handles only the most common renames — manual review is still required.
     *
     * @param oldProperties Map of old property key → value pairs
     * @return Map with renamed keys applied where known
     *
     * TODO: Review all application.properties / application.yml files manually.
     *       This method only covers a subset of renamed properties.
     */
    public static Map<String, String> migrateApplicationProperties(Map<String, String> oldProperties) {
        if (oldProperties == null) return new HashMap<>();
        Map<String, String> migrated = new HashMap<>();
        for (Map.Entry<String, String> entry : oldProperties.entrySet()) {
            String key = entry.getKey();
            String value = entry.getValue();
            if ("spring.elasticsearch.rest.uris".equals(key)) {
                migrated.put("spring.elasticsearch.uris", value);
                log.warn("Migrated property: {} → spring.elasticsearch.uris", key);
            } else if ("spring.elasticsearch.rest.username".equals(key)) {
                migrated.put("spring.elasticsearch.username", value);
                log.warn("Migrated property: {} → spring.elasticsearch.username", key);
            } else if ("spring.elasticsearch.rest.password".equals(key)) {
                migrated.put("spring.elasticsearch.password", value);
                log.warn("Migrated property: {} → spring.elasticsearch.password", key);
            } else if ("management.server.servlet.context-path".equals(key)) {
                migrated.put("management.server.base-path", value);
                log.warn("Migrated property: {} → management.server.base-path", key);
            } else if ("logging.file".equals(key)) {
                migrated.put("logging.file.name", value);
                log.warn("Migrated property: {} → logging.file.name", key);
            } else if ("logging.path".equals(key)) {
                migrated.put("logging.file.path", value);
                log.warn("Migrated property: {} → logging.file.path", key);
            } else if ("spring.mvc.pathmatch.use-suffix-pattern".equals(key)
                    || "spring.mvc.pathmatch.use-registered-suffix-pattern".equals(key)) {
                // TODO: These properties are removed in Spring Boot 3.x — suffix pattern matching unsupported.
                log.warn("REMOVED property (not migrated): {} — suffix pattern matching removed in Spring MVC 6.x", key);
            } else if ("spring.data.elasticsearch.cluster-name".equals(key)
                    || "spring.data.elasticsearch.cluster-nodes".equals(key)) {
                // TODO: These properties are removed — migrate to spring.elasticsearch.uris
                log.warn("REMOVED property (not migrated): {} — use spring.elasticsearch.uris", key);
            } else {
                migrated.put(key, value);
            }
        }
        return migrated;
    }

    // =========================================================================
    // SECTION 11: Java Version Migration (11 → 17+)
    // =========================================================================

    /**
     * Spring Boot 3.x requires Java 17 as minimum runtime.
     *
     * TODO: Update pom.xml java.version property and maven-compiler-plugin source/target:
     * <pre>
     *   &lt;properties&gt;
     *     &lt;java.version&gt;17&lt;/java.version&gt;
     *   &lt;/properties&gt;
     * </pre>
     *
     * TODO: Update Docker base image from adoptopenjdk/openjdk11-openj9:alpine to
     *       eclipse-temurin:17-jre-alpine or eclipse-temurin:21-jre-alpine.
     *       Breaking change: adoptopenjdk images are deprecated; use eclipse-temurin.
     *       Current: adoptopenjdk/openjdk11-openj9:alpine (JDK 11 OpenJ9)
     *       Target:  eclipse-temurin:17-jre-alpine or eclipse-temurin:21-jre-alpine
     *
     * TODO: Update CircleCI config to use Java 17+ executor image.
     *       Breaking change: Spring Boot 3.x will not start on JVM 11.
     */
    public static void javaVersionMigrationGuide() {
        log.warn("Java 17+ required for Spring Boot 3.x. Update pom.xml, Dockerfile, and CircleCI config.");
        log.warn("Replace adoptopenjdk/openjdk11-openj9:alpine with eclipse-temurin:17-jre-alpine.");
    }

    // =========================================================================
    // SECTION 12: Drools 7.32.0.Final → 8.x / 9.x Migration
    // =========================================================================

    /**
     * Drools 7.x → 8.x/9.x: Package and API changes.
     *
     * TODO: Evaluate Drools 8.x (kogito-based) vs Drools 9.x migration path.
     *       Breaking change: Drools 8.x introduced significant API restructuring.
     *       org.kie.* packages may have moved or been renamed.
     *
     * TODO: Update Drools BOM version in pom.xml:
     * <pre>
     *   &lt;dependency&gt;
     *     &lt;groupId&gt;org.drools&lt;/groupId&gt;
     *     &lt;artifactId&gt;drools-bom&lt;/artifactId&gt;
     *     &lt;version&gt;9.x.x.Final&lt;/version&gt; &lt;!-- or 8.x --&gt;
     *     &lt;type&gt;pom&lt;/type&gt;
     *     &lt;scope&gt;import&lt;/scope&gt;
     *   &lt;/dependency&gt;
     * </pre>
     *
     * TODO: Review KieServices, KieContainer, KieSession usage for API changes in Drools 8.x/9.x.
     *       Breaking change: Some KIE APIs restructured between Drools 7.x and 8.x.
     */
    public static void droolsMigrationGuide() {
        log.warn("Drools 7.32.0.Final → 8.x/9.x migration requires manual API review.");
        log.warn("Review KieServices, KieContainer, KieSession for breaking changes.");
    }

    // =========================================================================
    // SECTION 13: Multi-Module Maven Project Migration Notes
    // =========================================================================

    /**
     * Multi-module Maven project: Spring Boot 3.x parent POM migration.
     *
     * TODO: Update spring-boot-starter-parent version in root pom.xml:
     * <pre>
     *   &lt;parent&gt;
     *     &lt;groupId&gt;org.springframework.boot&lt;/groupId&gt;
     *     &lt;artifactId&gt;spring-boot-starter-parent&lt;/artifactId&gt;
     *     &lt;version&gt;3.3.x&lt;/version&gt; &lt;!-- replace x with latest patch --&gt;
     *   &lt;/parent&gt;
     * </pre>
     *
     * TODO: Ensure all child modules inherit the updated parent.
     *       Breaking change: Spring Boot 3.x manages different dependency versions than 2.5.x.
     *       Review all explicitly pinned dependency versions for conflicts with Spring Boot 3.x BOM.
     */
    public static void multiModuleMavenMigrationGuide() {
        log.warn("Update spring-boot-starter-parent to 3.3.x in root pom.xml.");
        log.warn("Review all child module dependency versions against Spring Boot 3.x BOM.");
    }

    // =========================================================================
    // SECTION 14: Migration Validation Checklist
    // =========================================================================

    /**
     * Prints a complete migration validation checklist to the log.
     * Run this at application startup during migration to surface all pending TODOs.
     *
     * TODO: Remove this call from production code once migration is complete.
     */
    public static void printMigrationChecklist() {
        log.warn("========================================================");
        log.warn("  Spring Boot 2.5.12 → 3.3.x Migration Checklist");
        log.warn("========================================================");
        log.warn("[ ] 1. Java version updated to 17+ in pom.xml, Dockerfile, CircleCI");
        log.warn("[ ] 2. spring-boot-starter-parent updated to 3.3.x");
        log.warn("[ ] 3. All javax.* EE imports replaced with jakarta.*");
        log.warn("[ ] 4. WebSecurityConfigurerAdapter removed, SecurityFilterChain @Bean added");
        log.warn("[ ] 5. antMatchers/mvcMatchers replaced with requestMatchers");
        log.warn("[ ] 6. authorizeRequests() replaced with authorizeHttpRequests()");
        log.warn("[ ] 7. PasswordEncoder @Bean explicitly declared");
        log.warn("[ ] 8. CSRF configuration reviewed for Spring Security 6.x");
        log.warn("[ ] 9. setUseTrailingSlashMatch() removed from WebMvcConfigurer");
        log.warn("[ ] 10. HttpMethod.resolve() replaced with HttpMethod.valueOf()");
        log.warn("[ ] 11. springfox-swagger2 removed, springdoc-openapi-starter-webmvc-ui 2.5.0 added");
        log.warn("[ ] 12. Springfox annotations replaced with springdoc/OpenAPI 3 annotations");
        log.warn("[ ] 13. Docket @Bean replaced with OpenAPI @Bean");
        log.warn("[ ] 14. Hibernate 6.x: javax.persistence → jakarta.persistence");
        log.warn("[ ] 15. Hibernate 6.x: naming strategy verified");
        log.warn("[ ] 16. Hibernate 6.x: org.hibernate.Criteria replaced with JPA CriteriaQuery");
        log.warn("[ ] 17. Hibernate 6.x: @Type annotations updated to class references");
        log.warn("[ ] 18. Hibernate 6.x: hbm.xml files migrated to annotations");
        log.warn("[ ] 19. JJWT updated to 0.12.6 (jjwt-api + jjwt-impl + jjwt-jackson)");
        log.warn("[ ] 20. JJWT API calls migrated to 0.12.x fluent API");
        log.warn("[ ] 21. Infinispan upgraded to 15.x OR migrated to Spring Cache + Redis");
        log.warn("[ ] 22. Infinispan config XML namespace updated");
        log.warn("[ ] 23. MapStruct updated to 1.6.2 (both mapstruct and mapstruct-processor)");
        log.warn("[ ] 24. @Mapper(componentModel = \"spring\") verified on all Spring mappers");
        log.warn("[ ] 25. commons-fileupload updated to 1.5+, fileCountMax set");
        log.warn("[ ] 26. application.properties keys migrated (see APPLICATION_PROPERTIES_RENAME_MAP)");
        log.warn("[ ] 27. Drools updated to 8.x/9.x, KIE API changes reviewed");
        log.warn("[ ] 28. Docker base image updated to eclipse-temurin:17-jre-alpine");
        log.warn("[ ] 29. CircleCI executor updated to Java 17+");
        log.warn("[ ] 30. All child module pom.xml files reviewed for dependency conflicts");
        log.warn("========================================================");
    }

    /**
     * Entry point for running migration guidance at startup.
     * Invoke from a @PostConstruct or ApplicationRunner during migration validation.
     *
     * TODO: Remove this invocation from production code after migration is complete.
     */
    public static void runMigrationGuidance() {
        printJavaxToJakartaMigrationGuide();
        securityConfigurerAdapterMigrationGuide();
        requestMatcherMigrationGuide();
        passwordEncoderMigrationGuide();
        csrfMigrationGuide();
        trailingSlashMigrationGuide();
        swaggerMigrationGuide();
        springdocConfigMigrationGuide();
        hibernateJakartaMigrationGuide();
        hibernateNamingStrategyMigrationGuide();
        hibernateCriteriaMigrationGuide();
        hibernateTypeMigrationGuide();
        hibernateHbmXmlMigrationGuide();
        jjwtMigrationGuide();
        infinispanMigrationGuide();
        redisCacheMigrationGuide();
        mapStructMigrationGuide();
        mapStructSpringComponentModelGuide();
        mapStructLombokOrderGuide();
        commonsFileUploadMigrationGuide();
        javaVersionMigrationGuide();
        droolsMigrationGuide();
        multiModuleMavenMigrationGuide();
        printMigrationChecklist();
    }
}