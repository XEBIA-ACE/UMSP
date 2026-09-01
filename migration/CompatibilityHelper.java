package com.shopizer.migration;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;

import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;

/**
 * MigrationCompatibilityShim
 *
 * Compatibility shim for Shopizer migration:
 *   Spring Boot 2.5.12 → 3.3.x
 *   Spring Security 5.5.x → 6.3.x
 *   Spring Data JPA 2.5.x → 3.3.x
 *   Springfox Swagger2 2.9.2 → springdoc-openapi 2.x
 *   Hibernate 5.4.x → 6.5.x
 *   Infinispan 9.4.18.Final → 15.x
 *   Drools 7.32.0.Final → 9.x
 *   jjwt 0.8.0 → 0.12.x
 *   commons-fileupload 1.3.3 → 1.5+
 *   PostgreSQL JDBC 42.2.18 → 42.7.x
 *
 * Usage: Call individual static helpers or MigrationCompatibilityShim.migrateConfig(oldConfig)
 *        to transform legacy configuration maps to the new format.
 *
 * TODO (GR-08): BCM scope gap — SME must validate scope boundaries before relying on this shim
 *               in production. All 324 Spring MVC endpoints must be smoke-tested post-migration.
 */
public final class MigrationCompatibilityShim {

    private static final Logger log = LoggerFactory.getLogger(MigrationCompatibilityShim.class);

    private MigrationCompatibilityShim() {
        // utility class
    }

    // =========================================================================
    // 1. javax → jakarta namespace migration
    // =========================================================================

    /**
     * Alias: previously callers imported javax.servlet.http.HttpServletRequest.
     * After Spring Boot 3.x the required import is jakarta.servlet.http.HttpServletRequest.
     *
     * TODO: Replace all source-level imports of javax.servlet.* with jakarta.servlet.*
     *       across every module in the multi-module Maven project.
     *       Automated sed/find-replace or OpenRewrite recipe "org.openrewrite.java.migrate.jakarta.JavaxServletToJakartaServlet"
     *       is recommended.
     *
     * This shim re-exports the jakarta types under the old simple names so that
     * any reflection-based code that references the string "javax.servlet" can be
     * redirected here during a transitional period.
     */
    public static Class<HttpServletRequest> javaxHttpServletRequestAlias() {
        // TODO: Remove this alias once all source files have been migrated to jakarta.servlet
        return HttpServletRequest.class;
    }

    public static Class<HttpServletResponse> javaxHttpServletResponseAlias() {
        // TODO: Remove this alias once all source files have been migrated to jakarta.servlet
        return HttpServletResponse.class;
    }

    // =========================================================================
    // 2. Spring Security 5.5.x → 6.3.x breaking changes
    // =========================================================================

    /**
     * Spring Security 6.x removed the deprecated WebSecurityConfigurerAdapter.
     * Callers must now expose SecurityFilterChain beans directly.
     *
     * TODO: Locate every class that extends WebSecurityConfigurerAdapter and
     *       refactor it to a @Configuration class that declares a
     *       SecurityFilterChain @Bean.  Example skeleton:
     *
     *   @Bean
     *   public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
     *       http.authorizeHttpRequests(auth -> auth
     *               .requestMatchers("/api/v1/**").authenticated()
     *               .anyRequest().permitAll())
     *           .csrf(csrf -> csrf.disable());
     *       return http.build();
     *   }
     *
     * Breaking change ref: Spring Security 6 migration guide §"WebSecurityConfigurerAdapter removed"
     */
    public static void webSecurityConfigurerAdapterRemoved() {
        throw new UnsupportedOperationException(
            "WebSecurityConfigurerAdapter has been removed in Spring Security 6. " +
            "Declare a SecurityFilterChain @Bean instead. " +
            "TODO: Migrate all WebSecurityConfigurerAdapter subclasses.");
    }

    /**
     * Spring Security 6 changed antMatchers/mvcMatchers/regexMatchers to requestMatchers.
     *
     * TODO: Replace all usages of:
     *   http.authorizeRequests().antMatchers(...)
     * with:
     *   http.authorizeHttpRequests().requestMatchers(...)
     *
     * Breaking change ref: Spring Security 6 migration guide §"authorizeRequests → authorizeHttpRequests"
     */
    public static String migrateAntMatcherToRequestMatcher(String antPattern) {
        // TODO: This is a documentation shim only. Actual source migration must be done manually
        //       or via OpenRewrite recipe "org.openrewrite.spring.security6.HttpSecurityLambdaDsl".
        log.warn("migrateAntMatcherToRequestMatcher called for pattern '{}'. " +
                 "Ensure source has been migrated to requestMatchers().", antPattern);
        return antPattern;
    }

    /**
     * Spring Security 6 deprecated SecurityContextHolder.getContext().getAuthentication()
     * in favour of injecting Authentication directly into controller methods, but the
     * static accessor still works.  This wrapper preserves the old call-site signature.
     *
     * TODO: Prefer injecting Authentication as a method parameter in @RestController methods
     *       rather than using the static SecurityContextHolder accessor.
     */
    public static Authentication getCurrentAuthentication() {
        return SecurityContextHolder.getContext().getAuthentication();
    }

    // =========================================================================
    // 3. jjwt 0.8.0 → 0.12.x API migration
    // =========================================================================

    /**
     * jjwt 0.8.0 used io.jsonwebtoken.impl.DefaultClaims and a fluent builder
     * that has changed significantly in 0.12.x.
     *
     * Old (0.8.0):
     *   Jwts.builder().setSubject(sub).signWith(SignatureAlgorithm.HS512, secret).compact()
     *
     * New (0.12.x):
     *   Jwts.builder().subject(sub).signWith(key).compact()
     *
     * TODO: Replace all usages of the deprecated setSubject/setExpiration/setIssuedAt
     *       builder methods with their 0.12.x equivalents: subject/expiration/issuedAt.
     *       Replace SignatureAlgorithm enum usages with MacAlgorithm / Keys.hmacShaKeyFor().
     *       Breaking change ref: jjwt 0.12.0 migration guide §"Builder method renames"
     *
     * TODO: Consider replacing jjwt entirely with Spring Security OAuth2 Resource Server
     *       (spring-security-oauth2-resource-server) for standardised JWT validation.
     *       Breaking change ref: upgrade target "Replace jjwt 0.8.0 with jjwt 0.12.x or
     *       spring-security OAuth2 resource server"
     */
    public static Map<String, Object> buildJwtMigrationNotes() {
        Map<String, Object> notes = new LinkedHashMap<>();
        notes.put("oldArtifact", "io.jsonwebtoken:jjwt:0.8.0");
        notes.put("newArtifact", "io.jsonwebtoken:jjwt-api:0.12.x + jjwt-impl + jjwt-jackson");
        notes.put("builderMethodRenames", Map.of(
            "setSubject()", "subject()",
            "setExpiration()", "expiration()",
            "setIssuedAt()", "issuedAt()",
            "setId()", "id()",
            "setIssuer()", "issuer()",
            "setAudience()", "audience()"
        ));
        notes.put("parserMethodRenames", Map.of(
            "Jwts.parser().setSigningKey(key)", "Jwts.parser().verifyWith(key).build()",
            "parseClaimsJws(token)", "parseSignedClaims(token)"
        ));
        notes.put("signatureAlgorithmMigration",
            "Replace SignatureAlgorithm.HS512 with Jwts.SIG.HS512; " +
            "use Keys.hmacShaKeyFor(secretBytes) to obtain a SecretKey.");
        // TODO: Remove this method once all JWT utility classes have been migrated
        return notes;
    }

    // =========================================================================
    // 4. Springfox 2.9.2 → springdoc-openapi 2.x migration
    // =========================================================================

    /**
     * Springfox 2.9.2 is abandoned and incompatible with Spring Boot 3.x.
     * All Springfox annotations and Docket beans must be replaced with
     * springdoc-openapi 2.x equivalents.
     *
     * TODO: Remove springfox-swagger2 and springfox-swagger-ui from all pom.xml files.
     *       Add:
     *         <dependency>
     *           <groupId>org.springdoc</groupId>
     *           <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
     *           <version>2.x.x</version>
     *         </dependency>
     *
     * TODO: Replace @EnableSwagger2 with @OpenAPIDefinition (or remove — springdoc auto-configures).
     * TODO: Replace springfox Docket @Bean with springdoc OpenAPI @Bean if customisation is needed.
     * TODO: Replace @ApiOperation with @Operation (io.swagger.v3.oas.annotations.Operation).
     * TODO: Replace @ApiParam with @Parameter (io.swagger.v3.oas.annotations.Parameter).
     * TODO: Replace @ApiModel / @ApiModelProperty with @Schema (io.swagger.v3.oas.annotations.media.Schema).
     * TODO: Replace @ApiResponse (springfox) with @ApiResponse (io.swagger.v3.oas.annotations.responses.ApiResponse).
     * TODO: Update swagger-ui URL from /swagger-ui.html to /swagger-ui/index.html.
     *
     * Breaking change ref: upgrade target "Replace abandoned Springfox 2.9.2 with springdoc-openapi 2.x"
     */
    public static Map<String, String> springfoxToSpringdocAnnotationMap() {
        Map<String, String> map = new LinkedHashMap<>();
        map.put("@EnableSwagger2", "@OpenAPIDefinition (or remove — auto-configured)");
        map.put("springfox.documentation.spring.web.plugins.Docket",
                "org.springdoc.core.models.GroupedOpenApi or io.swagger.v3.oas.models.OpenAPI @Bean");
        map.put("@ApiOperation", "@io.swagger.v3.oas.annotations.Operation");
        map.put("@ApiParam", "@io.swagger.v3.oas.annotations.Parameter");
        map.put("@ApiModel", "@io.swagger.v3.oas.annotations.media.Schema");
        map.put("@ApiModelProperty", "@io.swagger.v3.oas.annotations.media.Schema (field-level)");
        map.put("@ApiResponse (springfox)", "@io.swagger.v3.oas.annotations.responses.ApiResponse");
        map.put("@ApiIgnore", "@io.swagger.v3.oas.annotations.Hidden");
        map.put("/swagger-ui.html", "/swagger-ui/index.html");
        // TODO: Remove this method once all 324 endpoint controllers have been migrated
        return map;
    }

    // =========================================================================
    // 5. Hibernate 5.4.x → 6.5.x breaking changes
    // =========================================================================

    /**
     * Hibernate 6 changed the default implicit naming strategy and removed several
     * deprecated APIs.
     *
     * TODO: If the application relied on Hibernate 5's default naming strategy, add:
     *   spring.jpa.hibernate.naming.physical-strategy=
     *     org.hibernate.boot.model.naming.PhysicalNamingStrategyStandardImpl
     *   to application.properties to preserve existing table/column names.
     *
     * TODO: Replace usages of org.hibernate.criterion.* (Criteria API removed in H6)
     *       with JPA Criteria API (jakarta.persistence.criteria.*) or JPQL.
     *
     * TODO: Replace org.hibernate.Query (deprecated) with jakarta.persistence.Query.
     *
     * TODO: Hibernate 6 changed the default SEQUENCE allocation size. Verify that
     *       all @SequenceGenerator definitions specify allocationSize explicitly to
     *       avoid ID generation gaps or conflicts with existing data.
     *       Breaking change ref: Hibernate 6 migration guide §"Sequence allocation size"
     *
     * TODO: Verify all 65 JPA entities (identified in pre-migration snapshot) compile
     *       and map correctly under Hibernate 6.5.x. Run the full JPA entity operation
     *       suite (18 operations identified in pre-migration snapshot).
     */
    public static Map<String, String> hibernateMigrationNotes() {
        Map<String, String> notes = new LinkedHashMap<>();
        notes.put("criteriaApiRemoved",
            "org.hibernate.criterion.* removed. Migrate to jakarta.persistence.criteria.*");
        notes.put("hibernateQueryDeprecated",
            "org.hibernate.Query replaced by jakarta.persistence.Query");
        notes.put("namingStrategy",
            "Verify spring.jpa.hibernate.naming.physical-strategy if table names must be preserved");
        notes.put("sequenceAllocationSize",
            "Explicitly set allocationSize on all @SequenceGenerator to avoid data corruption");
        notes.put("entityCount", "65 JPA entities must be validated post-migration");
        notes.put("entityOperations", "18 JPA entity operations must be regression-tested");
        // TODO: Remove this method once Hibernate 6 migration is verified in CI
        return notes;
    }

    // =========================================================================
    // 6. Spring Data JPA 2.5.x → 3.3.x breaking changes
    // =========================================================================

    /**
     * Spring Data JPA 3.x (part of Spring Boot 3.x) requires jakarta.persistence
     * and drops several deprecated repository base classes.
     *
     * TODO: Replace all imports of org.springframework.data.jpa.repository.support.QuerydslJpaRepository
     *       with org.springframework.data.jpa.repository.support.QuerydslJpaPredicateExecutor.
     *
     * TODO: CrudRepository.findById() now returns Optional<T> — verify all call sites
     *       handle the Optional correctly (this was already the case in 2.x but
     *       null-return assumptions from older code may still exist).
     *
     * TODO: Auditing: @EnableJpaAuditing and AuditorAware<T> remain supported but
     *       the AuditorAware bean must now be explicitly named if multiple exist.
     *
     * TODO: Pageable sort expressions using property paths must be validated against
     *       Hibernate 6 entity metamodel changes.
     *
     * Breaking change ref: Spring Data 3.0 migration guide §"Removed APIs"
     */
    public static void springDataJpaMigrationNotes() {
        // TODO: Remove this method once Spring Data JPA 3.x migration is verified
        log.info("Spring Data JPA 3.x migration notes logged. " +
                 "See Javadoc on MigrationCompatibilityShim.springDataJpaMigrationNotes().");
    }

    // =========================================================================
    // 7. Infinispan 9.4.18.Final → 15.x breaking changes
    // =========================================================================

    /**
     * Infinispan 15.x introduced significant API and configuration changes.
     *
     * TODO: Replace org.infinispan.manager.DefaultCacheManager constructor calls —
     *       the XML configuration schema changed between 9.x and 15.x.
     *       Use the new GlobalConfigurationBuilder / ConfigurationBuilder fluent API.
     *
     * TODO: Infinispan 15.x requires the cache configuration XML namespace to be updated:
     *       Old: urn:infinispan:config:9.4
     *       New: urn:infinispan:config:15.0
     *
     * TODO: The org.infinispan.commons.marshall.jboss.GenericJBossMarshaller has been
     *       removed. Replace with ProtoStream marshaller or configure
     *       org.infinispan.commons.marshall.JavaSerializationMarshaller with an
     *       explicit allowlist for serialised classes.
     *
     * TODO: Verify Infinispan Spring Boot starter version aligns with Infinispan 15.x:
     *       infinispan-spring-boot3-starter-embedded or infinispan-spring-boot3-starter-remote.
     *
     * Breaking change ref: Infinispan 15 migration guide §"Configuration schema changes"
     *                      and §"Marshalling changes"
     */
    public static Map<String, String> infinispanConfigMigration(Map<String, String> oldConfig) {
        Map<String, String> newConfig = new HashMap<>(oldConfig);

        // Migrate XML namespace version reference stored as a config key
        if (newConfig.containsKey("infinispan.config.schema.version")) {
            String oldVersion = newConfig.get("infinispan.config.schema.version");
            log.warn("Migrating Infinispan config schema version from '{}' to '15.0'", oldVersion);
            newConfig.put("infinispan.config.schema.version", "15.0");
        }

        // Migrate marshaller class name
        if (newConfig.containsKey("infinispan.marshaller")) {
            String oldMarshaller = newConfig.get("infinispan.marshaller");
            if (oldMarshaller != null && oldMarshaller.contains("GenericJBossMarshaller")) {
                log.warn("GenericJBossMarshaller removed in Infinispan 15. " +
                         "Replacing with JavaSerializationMarshaller. " +
                         "TODO: Configure serialisation allowlist for security.");
                newConfig.put("infinispan.marshaller",
                    "org.infinispan.commons.marshall.JavaSerializationMarshaller");
                // TODO: Add infinispan.serialization.allowlist.classes with all serialised types
            }
        }

        // TODO: Validate all remaining Infinispan cache configuration keys against
        //       the Infinispan 15.x GlobalConfigurationBuilder / ConfigurationBuilder API.
        return newConfig;
    }

    // =========================================================================
    // 8. Drools 7.32.0.Final → 9.x breaking changes
    // =========================================================================

    /**
     * Drools 9.x (part of the kogito/drools realignment) introduced package and
     * API changes.
     *
     * TODO: The org.kie.api.KieServices / KieContainer / KieSession API is retained
     *       in Drools 9.x but the Maven artifact coordinates changed:
     *       Old: org.drools:drools-core:7.32.0.Final
     *       New: org.drools:drools-core:9.x.x (verify exact version on Maven Central)
     *
     * TODO: Replace org.kie:kie-spring (removed) with the Drools 9.x CDI/Spring
     *       integration module if Spring-managed KieSessions are used.
     *
     * TODO: DRL syntax: verify all .drl rule files compile under Drools 9.x.
     *       The exec-model is now the default; rules relying on legacy interpreted
     *       mode may need adjustment.
     *
     * TODO: KieScanner usage must be re-validated — artifact resolution behaviour
     *       changed in Drools 9.x.
     *
     * Breaking change ref: Drools 9 migration guide §"Exec model as default"
     *                      and §"kie-spring removal"
     */
    public static void droolsMigrationNotes() {
        // TODO: Remove this method once Drools 9.x migration is verified in CI
        log.info("Drools 9.x migration notes: see Javadoc on MigrationCompatibilityShim.droolsMigrationNotes().");
    }

    // =========================================================================
    // 9. commons-fileupload 1.3.3 → 1.5+ (CVE-2023-24998)
    // =========================================================================

    /**
     * commons-fileupload 1.3.3 is vulnerable to CVE-2023-24998 (unbounded multipart
     * request DoS). Version 1.5+ introduces a mandatory file-count limit.
     *
     * TODO: Update pom.xml dependency:
     *   <dependency>
     *     <groupId>commons-fileupload</groupId>
     *     <artifactId>commons-fileupload</artifactId>
     *     <version>1.5</version>
     *   </dependency>
     *
     * TODO: In Spring Boot 3.x, multipart handling is provided by the servlet container
     *       (StandardServletMultipartResolver). Verify that any explicit CommonsMultipartResolver
     *       bean is removed or replaced, as CommonsMultipartResolver is no longer
     *       auto-configured in Spring Framework 6.x.
     *
     * TODO: If CommonsMultipartResolver is still required, set FileUpload.setFileCountMax()
     *       to a safe limit (e.g. 10) to mitigate CVE-2023-24998.
     *
     * Breaking change ref: CVE-2023-24998; Spring Framework 6 §"CommonsMultipartResolver removed from auto-config"
     */
    public static void commonsFileUploadMigrationNotes() {
        // TODO: Remove this method once commons-fileupload 1.5+ is confirmed in all pom.xml files
        log.info("commons-fileupload migration notes: see Javadoc on " +
                 "MigrationCompatibilityShim.commonsFileUploadMigrationNotes().");
    }

    // =========================================================================
    // 10. PostgreSQL JDBC 42.2.18 → 42.7.x (SQL injection CVEs)
    // =========================================================================

    /**
     * PostgreSQL JDBC driver 42.2.18 contains SQL injection CVEs remediated in 42.7.x.
     *
     * TODO: Update pom.xml dependency (or rely on Spring Boot 3.3.x managed version):
     *   <dependency>
     *     <groupId>org.postgresql</groupId>
     *     <artifactId>postgresql</artifactId>
     *     <version>42.7.x</version>
     *   </dependency>
     *
     * TODO: Verify JDBC URL format — no breaking changes in connection string format
     *       between 42.2.x and 42.7.x, but SSL default behaviour changed:
     *       sslmode defaults may differ; explicitly set sslmode=require in production.
     *
     * Breaking change ref: PostgreSQL JDBC changelog §42.3.x–42.7.x security advisories
     */
    public static void postgresqlJdbcMigrationNotes() {
        // TODO: Remove this method once PostgreSQL JDBC 42.7.x is confirmed in all pom.xml files
        log.info("PostgreSQL JDBC migration notes: see Javadoc on " +
                 "MigrationCompatibilityShim.postgresqlJdbcMigrationNotes().");
    }

    // =========================================================================
    // 11. Unified config migration entry point
    // =========================================================================

    /**
     * Transforms a legacy application configuration map (e.g. loaded from
     * application.properties or a custom config store) to the new format
     * required by Spring Boot 3.3.x and the upgraded dependencies.
     *
     * @param oldConfig key-value pairs from the pre-migration configuration
     * @return migrated key-value pairs suitable for the post-migration application
     */
    public static Map<String, String> migrateConfig(Map<String, String> oldConfig) {
        Map<String, String> newConfig = new HashMap<>(oldConfig);

        // --- Spring Boot 3.x property renames ---

        // spring.datasource.initialization-mode → spring.sql.init.mode
        if (newConfig.containsKey("spring.datasource.initialization-mode")) {
            String value = newConfig.remove("spring.datasource.initialization-mode");
            newConfig.put("spring.sql.init.mode", value);
            log.info("Migrated: spring.datasource.initialization-mode → spring.sql.init.mode = {}", value);
        }

        // spring.datasource.schema → spring.sql.init.schema-locations
        if (newConfig.containsKey("spring.datasource.schema")) {
            String value = newConfig.remove("spring.datasource.schema");
            newConfig.put("spring.sql.init.schema-locations", value);
            log.info("Migrated: spring.datasource.schema → spring.sql.init.schema-locations = {}", value);
        }

        // spring.datasource.data → spring.sql.init.data-locations
        if (newConfig.containsKey("spring.datasource.data")) {
            String value = newConfig.remove("spring.datasource.data");
            newConfig.put("spring.sql.init.data-locations", value);
            log.info("Migrated: spring.datasource.data → spring.sql.init.data-locations = {}", value);
        }

        // spring.jpa.properties.hibernate.dialect — Hibernate 6 auto-detects dialect;
        // explicit dialect classes were renamed/removed.
        if (newConfig.containsKey("spring.jpa.properties.hibernate.dialect")) {
            String dialect = newConfig.get("spring.jpa.properties.hibernate.dialect");
            if (dialect != null && dialect.contains("org.hibernate.dialect.PostgreSQL")) {
                // PostgreSQL82Dialect, PostgreSQL9Dialect etc. removed in Hibernate 6
                newConfig.put("spring.jpa.properties.hibernate.dialect",
                    "org.hibernate.dialect.PostgreSQLDialect");
                log.warn("Migrated Hibernate dialect from '{}' to 'org.hibernate.dialect.PostgreSQLDialect'. " +
                         "TODO: Verify this is correct for your PostgreSQL version.", dialect);
            }
            // TODO: Add additional dialect migrations for MySQL, H2, etc. if used
        }

        // spring.security.oauth2.resourceserver — jjwt-based JWT config migration hint
        if (newConfig.containsKey("shopizer.jwt.secret")) {
            log.warn("shopizer.jwt.secret detected. " +
                     "TODO: Migrate JWT handling from jjwt 0.8.0 to jjwt 0.12.x or " +
                     "Spring Security OAuth2 Resource Server. " +
                     "See MigrationCompatibilityShim.buildJwtMigrationNotes().");
        }

        // management.endpoints.web.exposure.include — actuator path changed in Boot 3
        if (newConfig.containsKey("management.endpoints.web.base-path")) {
            String value = newConfig.get("management.endpoints.web.base-path");
            log.info("management.endpoints.web.base-path='{}' — verify actuator security " +
                     "configuration under Spring Security 6.x.", value);
            // TODO: Ensure actuator endpoints are secured via SecurityFilterChain requestMatchers
        }

        // Infinispan config migration
        Map<String, String> infinispanMigrated = infinispanConfigMigration(newConfig);
        newConfig.putAll(infinispanMigrated);

        // spring.mvc.pathmatch.use-suffix-pattern removed in Spring 6
        if (newConfig.containsKey("spring.mvc.pathmatch.use-suffix-pattern")) {
            String value = newConfig.remove("spring.mvc.pathmatch.use-suffix-pattern");
            log.warn("Removed spring.mvc.pathmatch.use-suffix-pattern='{}'. " +
                     "Suffix pattern matching was removed in Spring Framework 6. " +
                     "TODO: Update any URL patterns that relied on suffix matching " +
                     "(e.g. /resource.json) across all 324 endpoints.", value);
        }

        // spring.mvc.pathmatch.use-registered-suffix-pattern removed in Spring 6
        if (newConfig.containsKey("spring.mvc.pathmatch.use-registered-suffix-pattern")) {
            String value = newConfig.remove("spring.mvc.pathmatch.use-registered-suffix-pattern");
            log.warn("Removed spring.mvc.pathmatch.use-registered-suffix-pattern='{}'. " +
                     "TODO: Verify no registered suffix patterns are relied upon.", value);
        }

        // TODO: Add further property migrations as discovered during integration testing
        //       of the 324 Spring MVC endpoints across /api/v0/, /api/v1/, /api/v2/ namespaces.

        return newConfig;
    }

    // =========================================================================
    // 12. Smoke test endpoint inventory helper
    // =========================================================================

    /**
     * Returns the known API namespace prefixes for the 324 Spring MVC transactions
     * identified in the pre-migration snapshot. Use this list to drive smoke test
     * URL generation.
     *
     * TODO: Expand this list with the full 324 endpoint paths once extracted from
     *       CAST Imaging or the Spring MVC controller scan.
     * TODO: Validate all 324 endpoints return expected HTTP status codes post-migration.
     */
    public static String[] smokeTestApiNamespaces() {
        return new String[]{
            "/api/v0/",   // legacy: SystemRESTController, StoreContactRESTController
            "/api/v1/",   // primary: cart, order, customer, product, store, shipping, tax, user, content, catalog
            "/api/v2/",   // extended: ProductApiV2, ProductVariantApi, ProductVariantGroupApi, ProductVariationApi
            "/static/files/",
            "/static/products/",
            "/admin/files/"
        };
    }

    // =========================================================================
    // 13. Maven pom.xml migration checklist (documentation only)
    // =========================================================================

    /**
     * Returns a human-readable checklist of pom.xml changes required across the
     * multi-module Maven project.
     *
     * TODO: Apply each item in this checklist to every module pom.xml that declares
     *       the affected dependency.
     */
    public static String[] pomMigrationChecklist() {
        return new String[]{
            // TODO: Spring Boot parent version
            "Update <parent> spring-boot-starter-parent from 2.5.12 to 3.3.x",

            // TODO: Java version
            "Update <java.version> from 11 to 17 (minimum required by Spring Boot 3.x)",

            // TODO: javax → jakarta
            "Remove javax.servlet-api dependency; jakarta.servlet-api is provided by Spring Boot 3.x",

            // TODO: Springfox removal
            "Remove io.springfox:springfox-swagger2:2.9.2",
            "Remove io.springfox:springfox-swagger-ui:2.9.2",
            "Add org.springdoc:springdoc-openapi-starter-webmvc-ui:2.x.x",

            // TODO: jjwt upgrade
            "Replace io.jsonwebtoken:jjwt:0.8.0 with " +
                "io.jsonwebtoken:jjwt-api:0.12.x + jjwt-impl:0.12.x + jjwt-jackson:0.12.x",

            // TODO: commons-fileupload CVE
            "Upgrade commons-fileupload:commons-fileupload from 1.3.3 to 1.5",

            // TODO: PostgreSQL JDBC CVE
            "Upgrade org.postgresql:postgresql from 42.2.18 to 42.7.x",

            // TODO: Infinispan
            "Upgrade org.infinispan:infinispan-spring-boot-starter from 9.4.18.Final to 15.x " +
                "(use infinispan-spring-boot3-starter-embedded or -remote for Spring Boot 3 compatibility)",

            // TODO: Drools
            "Upgrade org.drools:drools-core and related from 7.32.0.Final to 9.x",
            "Remove org.kie:kie-spring if present; use Drools 9.x Spring integration module",

            // TODO: Hibernate (managed by Spring Boot 3.3.x — no explicit version needed unless overriding)
            "Remove explicit hibernate-core version override if present; " +
                "Spring Boot 3.3.x manages Hibernate 6.5.x",

            // TODO: Spring Security (managed by Spring Boot 3.3.x)
            "Remove explicit spring-security-* version overrides; " +
                "Spring Boot 3.3.x manages Spring Security 6.3.x"
        };
    }
}