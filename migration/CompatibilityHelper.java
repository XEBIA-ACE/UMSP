package com.shopizer.migration;

import jakarta.servlet.Filter;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.ServletRequest;
import jakarta.servlet.ServletResponse;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.util.matcher.AntPathRequestMatcher;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Properties;

/**
 * Shopizer Migration Helper / Compatibility Shim
 *
 * Addresses breaking changes for the following upgrades:
 *   - Spring Boot 2.5.12 → 3.4.1
 *   - Spring Security 5.5.x → 6.4.2
 *   - Spring Data JPA 2.5.x → 3.4.1
 *   - Hibernate 5.4.x → 6.6.4
 *   - Drools 7.32.0.Final → 9.44.0.Final
 *   - Springfox Swagger 2.9.2 → SpringDoc OpenAPI
 *   - javax.* → jakarta.* namespace migration
 *   - Java 11 → Java 21 (Eclipse Temurin)
 *   - PostgreSQL driver 42.2.18 → 42.7.x
 *   - jackson-core/databind → 2.18.x
 *   - commons-fileupload 1.3.3 → Spring Boot managed (CVE remediation)
 *   - jjwt 0.8.0 → replacement (CVE remediation)
 */
public class MigrationHelper {

    private static final Logger log = LoggerFactory.getLogger(MigrationHelper.class);

    // =========================================================================
    // 1. JAVAX → JAKARTA NAMESPACE MIGRATION
    // =========================================================================

    /**
     * Shim: javax.servlet.Filter → jakarta.servlet.Filter
     *
     * In Spring Boot 3.x, all javax.* imports must be replaced with jakarta.*
     * This adapter wraps legacy Filter implementations that still use the old
     * javax namespace (e.g., any custom filters in sm-shop).
     *
     * TODO: Manually scan all classes in sm-shop, sm-core, sm-core-modules for
     *       remaining `import javax.servlet.*` and replace with `import jakarta.servlet.*`
     *       Breaking change: Spring Boot 3.x requires Jakarta EE 9+ (jakarta namespace).
     *       Reference: Spring Boot 3.0 Migration Guide — javax to jakarta.
     */
    public static abstract class JakartaFilterAdapter implements Filter {

        @Override
        public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
                throws IOException, ServletException {
            doFilterInternal(
                    (HttpServletRequest) request,
                    (HttpServletResponse) response,
                    chain
            );
        }

        protected abstract void doFilterInternal(
                HttpServletRequest request,
                HttpServletResponse response,
                FilterChain chain
        ) throws IOException, ServletException;
    }

    // =========================================================================
    // 2. SPRING SECURITY 5.5.x → 6.4.2 BREAKING CHANGES
    // =========================================================================

    /**
     * Shim: WebSecurityConfigurerAdapter removal.
     *
     * Spring Security 6.x removed WebSecurityConfigurerAdapter entirely.
     * All security configuration must now use SecurityFilterChain beans.
     *
     * TODO: Locate all classes in sm-shop that extend
     *       `org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter`
     *       and refactor them to use the SecurityFilterChain bean pattern shown below.
     *       Breaking change: WebSecurityConfigurerAdapter was removed in Spring Security 6.0.
     *
     * TODO: Replace all usages of `antMatchers(...)` with `requestMatchers(...)`
     *       or `AntPathRequestMatcher` — antMatchers was removed in Spring Security 6.x.
     *
     * TODO: Replace `authorizeRequests()` with `authorizeHttpRequests()` in all
     *       HttpSecurity configurations across sm-shop security config classes.
     *
     * TODO: Replace `HttpSecurity.apply(customDsl)` with `HttpSecurity.with(customDsl, ...)`
     *       if any custom DSL configurers are used in sm-shop.
     *
     * TODO: Review CSRF configuration — Spring Security 6.x changed defaults.
     *       `csrf().disable()` syntax is unchanged but `CsrfConfigurer` API changed.
     *
     * TODO: Replace `UsernamePasswordAuthenticationFilter` subclass overrides if present —
     *       constructor signature changed in Spring Security 6.x.
     *
     * TODO: `SecurityContextHolder` strategy and `SecurityContextRepository` wiring
     *       changed in Spring Security 6.x. Review any custom SecurityContext persistence.
     */
    @Configuration
    @EnableWebSecurity
    public static class SecurityFilterChainShim {

        /**
         * Example SecurityFilterChain bean replacing WebSecurityConfigurerAdapter.
         * TODO: Replace this stub with the actual security rules from the existing
         *       WebSecurityConfigurerAdapter subclass(es) in sm-shop.
         */
        @Bean
        public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
            http
                // TODO: Migrate all antMatchers() calls to requestMatchers()
                .authorizeHttpRequests(authorize -> authorize
                    .requestMatchers(new AntPathRequestMatcher("/api/v1/public/**")).permitAll()
                    .requestMatchers(new AntPathRequestMatcher("/swagger-ui/**")).permitAll()
                    .requestMatchers(new AntPathRequestMatcher("/v3/api-docs/**")).permitAll()
                    // TODO: Add remaining URL authorization rules from legacy config
                    .anyRequest().authenticated()
                )
                // TODO: Configure JWT filter chain as appropriate for sm-shop
                .csrf(csrf -> csrf.disable());
            return http.build();
        }
    }

    // =========================================================================
    // 3. SPRINGFOX SWAGGER 2.9.2 → SPRINGDOC OPENAPI
    // =========================================================================

    /**
     * Shim: Springfox Swagger → SpringDoc OpenAPI
     *
     * Springfox is incompatible with Spring Boot 3.x. It must be replaced with
     * SpringDoc OpenAPI (org.springdoc:springdoc-openapi-starter-webmvc-ui).
     *
     * TODO: Remove springfox-swagger2 and springfox-swagger-ui from ALL pom.xml files
     *       in sm-shop and any other modules that declare them.
     *       Breaking change: Springfox does not support Spring Boot 3.x / Spring 6.x.
     *
     * TODO: Add to sm-shop/pom.xml (or parent pom.xml):
     *       <dependency>
     *           <groupId>org.springdoc</groupId>
     *           <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
     *           <version>2.6.0</version>
     *       </dependency>
     *
     * TODO: Remove all classes annotated with @EnableSwagger2 in sm-shop.
     *       Replace with SpringDoc auto-configuration (no explicit @Enable annotation needed).
     *
     * TODO: Replace Springfox Docket bean definitions with SpringDoc OpenAPI bean:
     *       @Bean public OpenAPI shopizerOpenAPI() { return new OpenAPI()...; }
     *
     * TODO: Replace @ApiOperation, @ApiParam, @ApiResponse (io.swagger.annotations.*)
     *       with @Operation, @Parameter, @ApiResponse (io.swagger.v3.oas.annotations.*)
     *       across all REST controllers in sm-shop.
     *
     * TODO: Replace @Api(tags=...) with @Tag(name=...) on controller classes.
     *
     * TODO: Update Swagger UI URL from /swagger-ui.html to /swagger-ui/index.html
     *       in any documentation, tests, or security permit rules.
     *
     * TODO: Update API docs URL from /v2/api-docs to /v3/api-docs in any
     *       integration tests or external tooling.
     */
    public static class SpringdocMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
        // See TODO comments above for all required manual steps.
    }

    // =========================================================================
    // 4. HIBERNATE 5.4.x → 6.6.4 BREAKING CHANGES
    // =========================================================================

    /**
     * Shim: Hibernate 5 → 6 breaking changes.
     *
     * TODO: Replace all usages of `org.hibernate.criterion.*` (Criteria API) with
     *       JPA Criteria API (`jakarta.persistence.criteria.*`) or JPQL queries.
     *       Breaking change: Legacy Hibernate Criteria API was removed in Hibernate 6.
     *
     * TODO: Replace `org.hibernate.Query` with `jakarta.persistence.Query` or
     *       `org.hibernate.query.Query` (Hibernate 6 repackaged query types).
     *
     * TODO: Review all `@Type(type="...")` annotations — Hibernate 6 changed the
     *       type system. String-based type names are no longer supported.
     *       Use `@Type(JsonType.class)` style or built-in type annotations.
     *
     * TODO: Replace `org.hibernate.type.StringType.INSTANCE` and similar static
     *       type constants — removed in Hibernate 6. Use `StandardBasicTypes.*`.
     *
     * TODO: Review `@Formula` annotations — SQL dialect differences may apply
     *       between Hibernate 5 and 6 for PostgreSQL.
     *
     * TODO: Replace `org.hibernate.annotations.TypeDef` / `@TypeDefs` — removed
     *       in Hibernate 6. Register custom types via `@Type` directly or
     *       via `MetadataBuilderContributor`.
     *
     * TODO: Review `@Cascade` usage — Hibernate 6 changed cascade type handling
     *       for some edge cases. Prefer JPA `cascade` attribute on relationships.
     *
     * TODO: Review `@NaturalId` and `@NaturalIdCache` usage — API changed in Hibernate 6.
     *
     * TODO: Review `hbm.xml` mapping files if any exist in sm-core-model —
     *       Hibernate 6 deprecated hbm.xml support. Migrate to annotations.
     *
     * TODO: Update `spring.jpa.properties.hibernate.dialect` in application.properties
     *       if explicitly set. Hibernate 6 auto-detects dialect; explicit dialect class
     *       names changed (e.g., PostgreSQL95Dialect → PostgreSQLDialect).
     */
    public static class HibernateMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 5. SPRING DATA JPA 2.5.x → 3.4.1 BREAKING CHANGES
    // =========================================================================

    /**
     * Shim: Spring Data JPA 2.5.x → 3.4.1 breaking changes.
     *
     * TODO: Replace `org.springframework.data.repository.CrudRepository` usages
     *       that rely on `Optional`-returning methods — API is unchanged but
     *       verify all repository return types compile under Spring Data 3.x.
     *
     * TODO: Replace `org.springframework.data.jpa.repository.query.QueryUtils`
     *       usages if present — some utility methods were removed or moved.
     *
     * TODO: Review `Pageable` and `Sort` usage — `PageRequest.of(...)` API is
     *       unchanged but `Sort.Direction` handling changed for some edge cases.
     *
     * TODO: Replace `org.springframework.data.domain.ExampleMatcher` usages if
     *       the `withIgnoreNullValues()` / `withIncludeNullValues()` API is used —
     *       method signatures changed in Spring Data 3.x.
     *
     * TODO: Review all `@Query` native queries for PostgreSQL compatibility with
     *       the upgraded PostgreSQL driver (42.7.x).
     *
     * TODO: `JpaRepository.getOne(id)` was removed — replace with `getReferenceById(id)`.
     *       Breaking change: getOne() was deprecated in Spring Data 2.x and removed in 3.x.
     *
     * TODO: `JpaRepository.getById(id)` was removed — replace with `getReferenceById(id)`.
     *       Breaking change: getById() was deprecated in Spring Data 2.x and removed in 3.x.
     */
    public static class SpringDataMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 6. DROOLS 7.32.0.Final → 9.44.0.Final BREAKING CHANGES
    // =========================================================================

    /**
     * Shim: Drools 7 → 9 breaking changes.
     *
     * TODO: Replace `org.kie.api.KieServices.Factory.get()` — KieServices API
     *       changed in Drools 9. Verify factory method availability.
     *
     * TODO: Replace `org.drools.compiler.*` imports — package structure changed
     *       significantly between Drools 7 and 9. Many classes moved to
     *       `org.drools.drl.*` or `org.kie.internal.*`.
     *
     * TODO: Review all `.drl` rule files in sm-core-modules for syntax changes.
     *       Drools 9 uses a stricter DRL parser. `dialect "mvel"` and `dialect "java"`
     *       handling changed.
     *
     * TODO: Replace `KieContainer.newKieSession()` with the updated session
     *       management API if the container lifecycle changed in Drools 9.
     *
     * TODO: Update `kmodule.xml` files — Drools 9 changed the kmodule schema.
     *       Validate against the new XSD.
     *
     * TODO: Replace `org.kie.api.runtime.KieSession.fireAllRules()` — API is
     *       nominally the same but verify agenda filter compatibility.
     *
     * TODO: Review `@Rule` and `@Fact` annotations if used — Drools 9 changed
     *       annotation processing for rule units.
     *
     * TODO: Update Maven dependency coordinates:
     *       Old: org.kie:kie-api:7.32.0.Final
     *       New: org.kie:kie-api:9.44.0.Final (verify exact artifact IDs for Drools 9)
     *       Note: Drools 9 may use different groupId/artifactId — confirm with
     *       https://www.drools.org/download/download.html
     */
    public static class DroolsMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 7. JWT LIBRARY MIGRATION (jjwt 0.8.0 → CVE remediation)
    // =========================================================================

    /**
     * Shim: jjwt 0.8.0 → io.jsonwebtoken:jjwt-api:0.12.x (CVE remediation)
     *
     * jjwt 0.8.0 contains critical CVEs. The API changed significantly in 0.10+.
     *
     * TODO: Replace `io.jsonwebtoken:jjwt:0.8.0` in pom.xml with:
     *       <dependency>
     *           <groupId>io.jsonwebtoken</groupId>
     *           <artifactId>jjwt-api</artifactId>
     *           <version>0.12.6</version>
     *       </dependency>
     *       <dependency>
     *           <groupId>io.jsonwebtoken</groupId>
     *           <artifactId>jjwt-impl</artifactId>
     *           <version>0.12.6</version>
     *           <scope>runtime</scope>
     *       </dependency>
     *       <dependency>
     *           <groupId>io.jsonwebtoken</groupId>
     *           <artifactId>jjwt-jackson</artifactId>
     *           <version>0.12.6</version>
     *           <scope>runtime</scope>
     *       </dependency>
     *
     * TODO: Replace `Jwts.parser().setSigningKey(secret).parseClaimsJws(token)`
     *       with `Jwts.parser().verifyWith(secretKey).build().parseSignedClaims(token)`
     *       Breaking change: jjwt 0.10+ changed the parser builder API entirely.
     *
     * TODO: Replace `Jwts.builder().setSubject(...).signWith(SignatureAlgorithm.HS512, secret)`
     *       with `Jwts.builder().subject(...).signWith(secretKey, Jwts.SIG.HS512).compact()`
     *       Breaking change: SignatureAlgorithm enum and signWith() signature changed in 0.10+.
     *
     * TODO: Replace `Claims.getSubject()` — method is unchanged but Claims is now
     *       obtained from `parseSignedClaims(...).getPayload()` not `.getBody()`.
     *       Breaking change: getBody() was removed in jjwt 0.12.x.
     */
    public static class JwtMigrationShim {

        /**
         * Compatibility constant: maps old SignatureAlgorithm string names to new API names.
         * TODO: Replace all direct usages with the new jjwt 0.12.x API.
         */
        public static final Map<String, String> ALGORITHM_MIGRATION_MAP;

        static {
            ALGORITHM_MIGRATION_MAP = new LinkedHashMap<>();
            ALGORITHM_MIGRATION_MAP.put("HS256", "Jwts.SIG.HS256");
            ALGORITHM_MIGRATION_MAP.put("HS384", "Jwts.SIG.HS384");
            ALGORITHM_MIGRATION_MAP.put("HS512", "Jwts.SIG.HS512");
            ALGORITHM_MIGRATION_MAP.put("RS256", "Jwts.SIG.RS256");
            ALGORITHM_MIGRATION_MAP.put("RS384", "Jwts.SIG.RS384");
            ALGORITHM_MIGRATION_MAP.put("RS512", "Jwts.SIG.RS512");
        }
    }

    // =========================================================================
    // 8. COMMONS-FILEUPLOAD CVE REMEDIATION
    // =========================================================================

    /**
     * Shim: commons-fileupload 1.3.3 → Spring Boot managed multipart (CVE remediation)
     *
     * commons-fileupload 1.3.3 contains critical CVEs (CVE-2016-1000031, etc.).
     * Spring Boot 3.x manages its own multipart support via jakarta.servlet.
     *
     * TODO: Remove `commons-fileupload:commons-fileupload:1.3.3` from ALL pom.xml files.
     *       Breaking change: commons-fileupload 1.x uses javax.servlet; incompatible with
     *       Spring Boot 3.x / Jakarta EE 9+.
     *
     * TODO: Replace any direct usage of `org.apache.commons.fileupload.FileItem`,
     *       `org.apache.commons.fileupload.servlet.ServletFileUpload`, etc. with
     *       Spring's `org.springframework.web.multipart.MultipartFile` API.
     *
     * TODO: If commons-fileupload is required as a transitive dependency, add an
     *       explicit exclusion and upgrade to commons-fileupload 2.0.0-M2+ which
     *       supports jakarta.servlet. Verify artifact coordinates for 2.x release.
     *
     * TODO: Update any Spring MVC multipart resolver configuration:
     *       Old: CommonsMultipartResolver bean
     *       New: StandardServletMultipartResolver (auto-configured by Spring Boot 3.x)
     *       or configure via spring.servlet.multipart.* properties.
     */
    public static class FileUploadMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 9. APPLICATION PROPERTIES / CONFIG FORMAT MIGRATION
    // =========================================================================

    /**
     * Migrates legacy application.properties keys to their Spring Boot 3.x equivalents.
     *
     * Transforms old Spring Boot 2.5.x property keys to Spring Boot 3.4.x keys.
     * Call this method to validate and rewrite your application.properties files.
     */
    public static Map<String, String> migrateApplicationProperties(Map<String, String> oldProperties) {
        Map<String, String> newProperties = new LinkedHashMap<>(oldProperties);

        // --- Spring Boot 3.x property renames ---

        // TODO: spring.datasource.initialization-mode was removed.
        //       Replace with spring.sql.init.mode
        migrateKey(newProperties,
                "spring.datasource.initialization-mode",
                "spring.sql.init.mode");

        // TODO: spring.datasource.schema / spring.datasource.data were removed.
        //       Replace with spring.sql.init.schema-locations / spring.sql.init.data-locations
        migrateKey(newProperties,
                "spring.datasource.schema",
                "spring.sql.init.schema-locations");
        migrateKey(newProperties,
                "spring.datasource.data",
                "spring.sql.init.data-locations");

        // TODO: spring.jpa.hibernate.use-new-id-generator-mappings was removed in Spring Boot 3.x.
        //       Hibernate 6 always uses the new ID generator mappings. Remove this property.
        if (newProperties.containsKey("spring.jpa.hibernate.use-new-id-generator-mappings")) {
            log.warn("[MIGRATION] Removing deprecated property: " +
                    "spring.jpa.hibernate.use-new-id-generator-mappings — " +
                    "Hibernate 6 always uses new ID generator mappings.");
            newProperties.remove("spring.jpa.hibernate.use-new-id-generator-mappings");
        }

        // TODO: spring.jpa.properties.hibernate.dialect — if set to a Hibernate 5 dialect class,
        //       update to Hibernate 6 equivalent.
        //       e.g., org.hibernate.dialect.PostgreSQL95Dialect → org.hibernate.dialect.PostgreSQLDialect
        migrateHibernateDialect(newProperties);

        // TODO: spring.security.oauth2.* properties — review if OAuth2 is used in sm-shop.
        //       Spring Security 6.x changed some OAuth2 property keys.

        // TODO: management.server.* and management.endpoint.* — Spring Boot 3.x changed
        //       some Actuator property keys. Review actuator configuration in sm-shop.

        // TODO: spring.mvc.pathmatch.use-suffix-pattern was removed in Spring Boot 3.x.
        //       Remove this property if present.
        if (newProperties.containsKey("spring.mvc.pathmatch.use-suffix-pattern")) {
            log.warn("[MIGRATION] Removing deprecated property: " +
                    "spring.mvc.pathmatch.use-suffix-pattern — removed in Spring Boot 3.x.");
            newProperties.remove("spring.mvc.pathmatch.use-suffix-pattern");
        }

        // TODO: spring.mvc.pathmatch.use-registered-suffix-pattern was removed in Spring Boot 3.x.
        if (newProperties.containsKey("spring.mvc.pathmatch.use-registered-suffix-pattern")) {
            log.warn("[MIGRATION] Removing deprecated property: " +
                    "spring.mvc.pathmatch.use-registered-suffix-pattern — removed in Spring Boot 3.x.");
            newProperties.remove("spring.mvc.pathmatch.use-registered-suffix-pattern");
        }

        // TODO: spring.redis.* properties were renamed to spring.data.redis.* in Spring Boot 3.x.
        migrateKeyPrefix(newProperties, "spring.redis.", "spring.data.redis.");

        // TODO: spring.elasticsearch.rest.* was renamed to spring.elasticsearch.* in Spring Boot 3.x.
        migrateKeyPrefix(newProperties, "spring.elasticsearch.rest.", "spring.elasticsearch.");

        // TODO: spring.flyway.* — review Flyway configuration if used.
        //       Flyway 9+ (used by Spring Boot 3.x) changed some property keys.

        // TODO: logging.file was renamed to logging.file.name in Spring Boot 2.2+.
        //       Ensure this was already migrated; Spring Boot 3.x removed the old key.
        migrateKey(newProperties, "logging.file", "logging.file.name");

        // TODO: logging.path was renamed to logging.file.path in Spring Boot 2.2+.
        migrateKey(newProperties, "logging.path", "logging.file.path");

        return newProperties;
    }

    private static void migrateKey(Map<String, String> props, String oldKey, String newKey) {
        if (props.containsKey(oldKey)) {
            String value = props.remove(oldKey);
            props.put(newKey, value);
            log.info("[MIGRATION] Renamed property: {} → {} = {}", oldKey, newKey, value);
        }
    }

    private static void migrateKeyPrefix(Map<String, String> props, String oldPrefix, String newPrefix) {
        Map<String, String> toAdd = new LinkedHashMap<>();
        props.entrySet().removeIf(entry -> {
            if (entry.getKey().startsWith(oldPrefix)) {
                String newKey = newPrefix + entry.getKey().substring(oldPrefix.length());
                toAdd.put(newKey, entry.getValue());
                log.info("[MIGRATION] Renamed property prefix: {} → {}", entry.getKey(), newKey);
                return true;
            }
            return false;
        });
        props.putAll(toAdd);
    }

    private static void migrateHibernateDialect(Map<String, String> props) {
        String dialectKey = "spring.jpa.properties.hibernate.dialect";
        if (props.containsKey(dialectKey)) {
            String dialect = props.get(dialectKey);
            Map<String, String> dialectMap = new HashMap<>();
            // Hibernate 5 → Hibernate 6 dialect class renames
            dialectMap.put("org.hibernate.dialect.PostgreSQL95Dialect",
                    "org.hibernate.dialect.PostgreSQLDialect");
            dialectMap.put("org.hibernate.dialect.PostgreSQL10Dialect",
                    "org.hibernate.dialect.PostgreSQLDialect");
            dialectMap.put("org.hibernate.dialect.PostgreSQL9Dialect",
                    "org.hibernate.dialect.PostgreSQLDialect");
            dialectMap.put("org.hibernate.dialect.MySQL57Dialect",
                    "org.hibernate.dialect.MySQLDialect");
            dialectMap.put("org.hibernate.dialect.MySQL8Dialect",
                    "org.hibernate.dialect.MySQLDialect");
            dialectMap.put("org.hibernate.dialect.H2Dialect",
                    "org.hibernate.dialect.H2Dialect"); // unchanged
            if (dialectMap.containsKey(dialect)) {
                String newDialect = dialectMap.get(dialect);
                props.put(dialectKey, newDialect);
                log.info("[MIGRATION] Updated Hibernate dialect: {} → {}", dialect, newDialect);
            } else {
                // TODO: Manually verify this Hibernate dialect is valid for Hibernate 6.6.4
                log.warn("[MIGRATION] Unknown Hibernate dialect '{}' — manually verify " +
                        "compatibility with Hibernate 6.6.4", dialect);
            }
        }
    }

    /**
     * Reads an application.properties file, applies migrations, and writes the result.
     *
     * Usage: MigrationHelper.migratePropertiesFile(
     *            Paths.get("sm-shop/src/main/resources/application.properties"),
     *            Paths.get("sm-shop/src/main/resources/application.properties.migrated")
     *        );
     */
    public static void migratePropertiesFile(Path inputPath, Path outputPath) throws IOException {
        Properties props = new Properties();
        try (InputStream is = Files.newInputStream(inputPath)) {
            props.load(is);
        }

        Map<String, String> propsMap = new LinkedHashMap<>();
        for (String name : props.stringPropertyNames()) {
            propsMap.put(name, props.getProperty(name));
        }

        Map<String, String> migrated = migrateApplicationProperties(propsMap);

        Properties migratedProps = new Properties();
        migratedProps.putAll(migrated);

        try (OutputStream os = Files.newOutputStream(outputPath)) {
            migratedProps.store(os,
                    "Migrated by MigrationHelper — Spring Boot 2.5.12 → 3.4.1\n" +
                    "# TODO: Review all TODO comments in MigrationHelper.java for manual steps.");
        }

        log.info("[MIGRATION] Properties file migrated: {} → {}", inputPath, outputPath);
    }

    // =========================================================================
    // 10. MAVEN POM MIGRATION GUIDANCE
    // =========================================================================

    /**
     * Documents required pom.xml changes across all modules.
     *
     * TODO: Update parent pom.xml Spring Boot version:
     *       <parent>
     *           <groupId>org.springframework.boot</groupId>
     *           <artifactId>spring-boot-starter-parent</artifactId>
     *           <version>3.4.1</version>  <!-- was 2.5.12 -->
     *       </parent>
     *
     * TODO: Update Java source/target version in parent pom.xml:
     *       <java.version>21</java.version>  <!-- was 11 -->
     *       <maven.compiler.source>21</maven.compiler.source>
     *       <maven.compiler.target>21</maven.compiler.target>
     *
     * TODO: Update PostgreSQL driver version:
     *       <dependency>
     *           <groupId>org.postgresql</groupId>
     *           <artifactId>postgresql</artifactId>
     *           <version>42.7.4</version>  <!-- was 42.2.18 -->
     *       </dependency>
     *
     * TODO: Update Jackson version (align with Spring Boot 3.4.1 managed version):
     *       Spring Boot 3.4.1 manages jackson-bom 2.18.x — remove explicit Jackson
     *       version overrides if present, or align to 2.18.x.
     *
     * TODO: Update Spring Security version (if explicitly declared):
     *       <version>6.4.2</version>  <!-- was 5.5.x -->
     *       Note: Spring Boot 3.4.1 manages Spring Security 6.4.x automatically.
     *       Remove explicit Spring Security version declarations if using Spring Boot parent.
     *
     * TODO: Update Drools/KIE version:
     *       <version>9.44.0.Final</version>  <!-- was 7.32.0.Final -->
     *       Verify exact artifact IDs for Drools 9 — groupId may have changed.
     *
     * TODO: Remove springfox-swagger2 and springfox-swagger-ui dependencies.
     *       Add springdoc-openapi-starter-webmvc-ui:2.6.0.
     *
     * TODO: Remove commons-fileupload:1.3.3 dependency (CVE remediation).
     *
     * TODO: Replace jjwt:0.8.0 with jjwt-api/jjwt-impl/jjwt-jackson:0.12.6.
     *
     * TODO: Update Docker base image in Dockerfile(s):
     *       Old: adoptopenjdk:11-jre-hotspot (or similar AdoptOpenJDK image)
     *       New: eclipse-temurin:21-jre-jammy (or eclipse-temurin:21-jre-alpine)
     *       Breaking change: AdoptOpenJDK Docker images are deprecated; use Eclipse Temurin.
     *
     * TODO: Update maven-wrapper.properties in all 5 modules to use Maven 3.9.x:
     *       distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/
     *           apache-maven/3.9.9/apache-maven-3.9.9-bin.zip
     *
     * TODO: Update Jenkins/CircleCI pipeline configurations:
     *       - Replace AdoptOpenJDK Docker image with Eclipse Temurin 21
     *       - Update JAVA_HOME paths if hardcoded
     *       - Update any Java version checks in CI scripts
     */
    public static class PomMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 11. INTEGRATION TEST MIGRATION GUIDANCE
    // =========================================================================

    /**
     * Documents required changes for integration tests.
     *
     * TODO: Replace `@RunWith(SpringRunner.class)` with `@ExtendWith(SpringExtension.class)`
     *       in all integration test classes. Spring Boot 3.x requires JUnit 5.
     *       Breaking change: JUnit 4 @RunWith is not supported in Spring Boot 3.x test slice.
     *
     * TODO: Replace `org.junit.Test` with `org.junit.jupiter.api.Test` in all test classes.
     *
     * TODO: Replace `org.junit.Assert.*` with `org.junit.jupiter.api.Assertions.*`.
     *
     * TODO: Replace `@Before` / `@After` with `@BeforeEach` / `@AfterEach`.
     *
     * TODO: Replace `@BeforeClass` / `@AfterClass` with `@BeforeAll` / `@AfterAll`.
     *
     * TODO: Review `@SpringBootTest` webEnvironment settings — default changed in Spring Boot 3.x.
     *
     * TODO: Review MockMvc test configurations — `MockMvcBuilders.standaloneSetup()`
     *       may need updates for Spring Security 6.x integration.
     *
     * TODO: Replace `org.springframework.test.web.servlet.result.MockMvcResultMatchers`
     *       usages that relied on Springfox endpoints (/v2/api-docs, /swagger-ui.html)
     *       with SpringDoc endpoints (/v3/api-docs, /swagger-ui/index.html).
     *
     * TODO: Review Testcontainers configuration if used — ensure PostgreSQL container
     *       image version is compatible with driver 42.7.x.
     */
    public static class IntegrationTestMigrationGuide {
        // This class is intentionally empty — it serves as a documentation anchor.
    }

    // =========================================================================
    // 12. MAIN ENTRY POINT (for standalone migration validation)
    // =========================================================================

    /**
     * Standalone migration validation runner.
     * Run this class directly to validate and migrate properties files.
     *
     * Usage: java -cp ... com.shopizer.migration.MigrationHelper
     */
    public static void main(String[] args) throws IOException {
        log.info("=== Shopizer Migration Helper ===");
        log.info("Spring Boot 2.5.12 → 3.4.1 | Spring Security 5.5.x → 6.4.2");
        log.info("Hibernate 5.4.x → 6.6.4 | Spring Data JPA 2.5.x → 3.4.1");
        log.info("Drools 7.32.0.Final → 9.44.0.Final | Java 11 → 21");
        log.info("");

        // Migrate properties files for all known modules
        String[] modules = {
            "sm-shop/src/main/resources",
            "sm-core/src/main/resources",
            "sm-core-modules/src/main/resources",
            "sm-shop-model/src/main/resources",
            "sm-core-model/src/main/resources"
        };

        for (String moduleResourceDir : modules) {
            Path propsPath = Paths.get(moduleResourceDir, "application.properties");
            if (Files.exists(propsPath)) {
                Path outputPath = Paths.get(moduleResourceDir, "application.properties.migrated");
                log.info("Migrating: {}", propsPath);
                migratePropertiesFile(propsPath, outputPath);
                log.info("Written to: {}", outputPath);
            } else {
                log.info("No application.properties found at: {}", propsPath);
            }
        }

        log.info("");
        log.info("=== Migration Helper Complete ===");
        log.info("IMPORTANT: Review all TODO comments in MigrationHelper.java");
        log.info("for manual intervention steps that cannot be automated.");
    }
}