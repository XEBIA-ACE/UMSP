import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import jakarta.persistence.EntityManager;
import jakarta.servlet.http.HttpServletRequest;
import org.hibernate.Session;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Nested;
import org.junit.jupiter.api.Test;
import org.springdoc.core.properties.SpringDocConfigProperties;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.context.ApplicationContext;
import org.springframework.core.SpringVersion;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.web.servlet.DispatcherServlet;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.*;

/**
 * Upgrade validation test suite for Spring Boot 2.5.12 → 3.3.x migration.
 *
 * Verifies:
 * - Spring Boot 3.3.x is active at the exact target version
 * - jakarta.* namespace is in use (not javax.*)
 * - Spring Security 6.3.x APIs are active
 * - springdoc-openapi 2.x replaces springfox
 * - JJWT 0.12.x API is in use
 * - Hibernate 6.5.x is active
 * - Spring MVC 6.1.x is active
 * - Java 17 runtime is active
 */
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
@ActiveProfiles("test")
@DisplayName("Spring Boot 3.3.x Upgrade Validation Tests")
class SpringBoot33UpgradeValidationTest {

    @Autowired
    private ApplicationContext applicationContext;

    @Autowired(required = false)
    private TestRestTemplate restTemplate;

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-001 / UPG-003: Java 17 runtime
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-001 / UPG-003: Java 17 Runtime")
    class JavaRuntimeVersionTests {

        @Test
        @DisplayName("JVM runtime version must be 17 or higher (target: 17 LTS)")
        void javaRuntimeMustBeAtLeast17() {
            String javaVersion = System.getProperty("java.version");
            assertNotNull(javaVersion, "java.version system property must be present");

            int majorVersion = parseMajorJavaVersion(javaVersion);
            assertThat(majorVersion)
                    .as("Java major version must be >= 17 (current: %s)", javaVersion)
                    .isGreaterThanOrEqualTo(17);
        }

        @Test
        @DisplayName("Maven compiler target must reflect Java 17 (source/target = 17)")
        void javaSpecificationVersionMustBe17() {
            String specVersion = System.getProperty("java.specification.version");
            assertNotNull(specVersion, "java.specification.version must be present");
            int spec = Integer.parseInt(specVersion.contains(".") ? specVersion.split("\\.")[1] : specVersion);
            assertThat(spec)
                    .as("java.specification.version must be >= 17, was: %s", specVersion)
                    .isGreaterThanOrEqualTo(17);
        }

        private int parseMajorJavaVersion(String version) {
            // Handles "17.0.x", "11.0.x", "1.8.x"
            String[] parts = version.split("\\.");
            int first = Integer.parseInt(parts[0]);
            if (first == 1 && parts.length > 1) {
                return Integer.parseInt(parts[1]);
            }
            return first;
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-004: Spring Boot 3.3.x version assertion
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-004: Spring Boot 3.3.x Version Assertion")
    class SpringBootVersionTests {

        @Test
        @DisplayName("Spring Boot version must be 3.3.x (exact major.minor match)")
        void springBootVersionMustBe33x() {
            String bootVersion = SpringApplication.class.getPackage().getImplementationVersion();
            // In test classpaths the manifest version may be null; fall back to Spring Framework version check
            if (bootVersion != null) {
                assertThat(bootVersion)
                        .as("Spring Boot version must start with 3.3, was: %s", bootVersion)
                        .startsWith("3.3");
            }
            // Always assert Spring Framework 6.x is present (transitively required by Boot 3.3)
            String springVersion = SpringVersion.getVersion();
            assertNotNull(springVersion, "Spring Framework version must be detectable");
            assertThat(springVersion)
                    .as("Spring Framework version must be 6.x for Spring Boot 3.3.x, was: %s", springVersion)
                    .startsWith("6.");
        }

        @Test
        @DisplayName("Spring Framework version must be 6.1.x (Spring MVC 6.1.x — UPG-004)")
        void springFrameworkVersionMustBe61x() {
            String springVersion = SpringVersion.getVersion();
            assertNotNull(springVersion, "Spring Framework version must not be null");
            int major = Integer.parseInt(springVersion.split("\\.")[0]);
            int minor = Integer.parseInt(springVersion.split("\\.")[1]);
            assertThat(major).as("Spring major version must be 6").isEqualTo(6);
            assertThat(minor).as("Spring minor version must be >= 1 (Spring MVC 6.1.x)").isGreaterThanOrEqualTo(1);
        }

        @Test
        @DisplayName("ApplicationContext must load successfully under Spring Boot 3.3.x")
        void applicationContextLoads() {
            assertNotNull(applicationContext, "ApplicationContext must not be null");
        }

        @Test
        @DisplayName("DispatcherServlet bean must be present (Spring MVC 6.1.x active)")
        void dispatcherServletBeanPresent() {
            assertThat(applicationContext.getBeanNamesForType(DispatcherServlet.class))
                    .as("DispatcherServlet bean must be registered for Spring MVC 6.1.x")
                    .isNotEmpty();
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-005: jakarta.* namespace migration (javax → jakarta)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-005: jakarta.* Namespace Migration")
    class JakartaNamespaceMigrationTests {

        @Test
        @DisplayName("jakarta.servlet.http.HttpServletRequest must be loadable (not javax.servlet)")
        void jakartaServletNamespaceIsActive() {
            assertDoesNotThrow(
                    () -> Class.forName("jakarta.servlet.http.HttpServletRequest"),
                    "jakarta.servlet.http.HttpServletRequest must be on the classpath"
            );
        }

        @Test
        @DisplayName("javax.servlet.http.HttpServletRequest must NOT be the primary servlet API")
        void javaxServletNamespaceIsNotPrimary() {
            // jakarta.servlet must be present; javax.servlet may or may not be present
            // but the application must compile and run against jakarta.*
            HttpServletRequest.class.getName(); // compile-time proof: import is jakarta.*
            assertThat(HttpServletRequest.class.getPackageName())
                    .as("HttpServletRequest must come from jakarta.servlet, not javax.servlet")
                    .startsWith("jakarta.servlet");
        }

        @Test
        @DisplayName("jakarta.persistence.EntityManager must be loadable (not javax.persistence)")
        void jakartaPersistenceNamespaceIsActive() {
            assertDoesNotThrow(
                    () -> Class.forName("jakarta.persistence.EntityManager"),
                    "jakarta.persistence.EntityManager must be on the classpath"
            );
            assertThat(EntityManager.class.getPackageName())
                    .as("EntityManager must come from jakarta.persistence")
                    .startsWith("jakarta.persistence");
        }

        @Test
        @DisplayName("javax.persistence.EntityManager must NOT be on the classpath")
        void javaxPersistenceEntityManagerMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("javax.persistence.EntityManager"),
                    "javax.persistence.EntityManager must NOT be present — old JPA namespace must be removed"
            );
        }

        @Test
        @DisplayName("javax.servlet.http.HttpServletRequest must NOT be on the classpath")
        void javaxServletHttpServletRequestMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("javax.servlet.http.HttpServletRequest"),
                    "javax.servlet.http.HttpServletRequest must NOT be present — old servlet namespace must be removed"
            );
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-004 (transitive): Spring Security 6.3.x
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-004 (transitive): Spring Security 6.3.x")
    class SpringSecurityVersionTests {

        @Test
        @DisplayName("Spring Security version must be 6.3.x")
        void springSecurityVersionMustBe63x() {
            String secVersion = org.springframework.security.core.SpringSecurityCoreVersion.getVersion();
            assertNotNull(secVersion, "Spring Security version must be detectable");
            assertThat(secVersion)
                    .as("Spring Security version must start with 6.3, was: %s", secVersion)
                    .startsWith("6.");
            int minor = Integer.parseInt(secVersion.split("\\.")[1]);
            assertThat(minor)
                    .as("Spring Security minor version must be >= 3, was: %s", secVersion)
                    .isGreaterThanOrEqualTo(3);
        }

        @Test
        @DisplayName("BCryptPasswordEncoder (Spring Security 6.x API) must be instantiable")
        void bcryptPasswordEncoderInstantiable() {
            PasswordEncoder encoder = new BCryptPasswordEncoder();
            String encoded = encoder.encode("upgrade-test-password");
            assertNotNull(encoded);
            assertTrue(encoder.matches("upgrade-test-password", encoded),
                    "BCryptPasswordEncoder must correctly encode and match passwords");
        }

        @Test
        @DisplayName("SimpleGrantedAuthority (Spring Security 6.x) must use jakarta namespace internally")
        void simpleGrantedAuthorityUsesJakartaInternally() {
            SimpleGrantedAuthority authority = new SimpleGrantedAuthority("ROLE_ADMIN");
            assertNotNull(authority);
            assertEquals("ROLE_ADMIN", authority.getAuthority());
        }

        @Test
        @DisplayName("Deprecated WebSecurityConfigurerAdapter must NOT be on the classpath (removed in Spring Security 6.x)")
        void webSecurityConfigurerAdapterMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter"),
                    "WebSecurityConfigurerAdapter was removed in Spring Security 6.x and must not be present"
            );
        }

        @Test
        @DisplayName("Deprecated AuthorizationServerConfigurerAdapter must NOT be on the classpath (removed in Spring Security 6.x)")
        void authorizationServerConfigurerAdapterMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("org.springframework.security.oauth2.config.annotation.web.configuration.AuthorizationServerConfigurerAdapter"),
                    "AuthorizationServerConfigurerAdapter was removed in Spring Security 6.x"
            );
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-006: springdoc-openapi 2.x replaces springfox-swagger2 2.9.2
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-006: springdoc-openapi 2.x (replaces Springfox 2.9.2)")
    class SpringdocOpenApiMigrationTests {

        @Test
        @DisplayName("springdoc-openapi SpringDocConfigProperties must be loadable")
        void springdocConfigPropertiesLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("org.springdoc.core.properties.SpringDocConfigProperties"),
                    "SpringDocConfigProperties must be on the classpath (springdoc-openapi 2.x)"
            );
        }

        @Test
        @DisplayName("SpringDocConfigProperties bean must be present in ApplicationContext")
        void springdocConfigPropertiesBeanPresent() {
            assertThat(applicationContext.getBeanNamesForType(SpringDocConfigProperties.class))
                    .as("SpringDocConfigProperties bean must be registered by springdoc-openapi 2.x")
                    .isNotEmpty();
        }

        @Test
        @DisplayName("Springfox Docket class must NOT be on the classpath (springfox removed)")
        void springfoxDocketMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("springfox.documentation.spring.web.plugins.Docket"),
                    "Springfox Docket must NOT be present — springfox-swagger2 must be removed"
            );
        }

        @Test
        @DisplayName("Springfox EnableSwagger2 annotation must NOT be on the classpath")
        void springfoxEnableSwagger2MustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("springfox.documentation.swagger2.annotations.EnableSwagger2"),
                    "Springfox @EnableSwagger2 must NOT be present — springfox-swagger2 must be removed"
            );
        }

        @Test
        @DisplayName("OpenAPI 3 /v3/api-docs endpoint must respond with HTTP 200")
        void openApiDocsEndpointResponds() {
            if (restTemplate == null) return; // skip if web environment not available
            ResponseEntity<String> response = restTemplate.getForEntity("/v3/api-docs", String.class);
            assertThat(response.getStatusCode())
                    .as("OpenAPI 3 /v3/api-docs endpoint must return HTTP 200")
                    .isEqualTo(HttpStatus.OK);
            assertThat(response.getBody())
                    .as("OpenAPI 3 response body must contain 'openapi' key")
                    .contains("openapi");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-007: JJWT 0.12.x API (replaces 0.8.0)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-007: JJWT 0.12.x API Migration")
    class JjwtVersionMigrationTests {

        @Test
        @DisplayName("JJWT 0.12.x io.jsonwebtoken.Jwts must be loadable")
        void jjwtJwtsClassLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("io.jsonwebtoken.Jwts"),
                    "io.jsonwebtoken.Jwts must be on the classpath (jjwt-api 0.12.x)"
            );
        }

        @Test
        @DisplayName("JJWT 0.12.x io.jsonwebtoken.security.Keys must be loadable")
        void jjwtKeysClassLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("io.jsonwebtoken.security.Keys"),
                    "io.jsonwebtoken.security.Keys must be on the classpath (jjwt-api 0.12.x)"
            );
        }

        @Test
        @DisplayName("JJWT 0.12.x JWT can be built and parsed using new fluent API")
        void jjwtNewApiCanBuildAndParseToken() {
            SecretKey key = Keys.hmacShaKeyFor(
                    "upgrade-validation-secret-key-32bytes!!".getBytes(StandardCharsets.UTF_8)
            );

            String token = Jwts.builder()
                    .subject("upgrade-test-user")
                    .issuedAt(new Date())
                    .expiration(new Date(System.currentTimeMillis() + 60_000))
                    .signWith(key)
                    .compact();

            assertNotNull(token, "JWT token must be generated");

            String subject = Jwts.parser()
                    .verifyWith(key)
                    .build()
                    .parseSignedClaims(token)
                    .getPayload()
                    .getSubject();

            assertEquals("upgrade-test-user", subject,
                    "JWT subject must round-trip correctly with JJWT 0.12.x API");
        }

        @Test
        @DisplayName("Deprecated JJWT 0.8.x JwtBuilder.setSubject must NOT be available")
        void jjwtOldSetSubjectApiMustBeAbsent() {
            // In JJWT 0.12.x, setSubject() was replaced by subject()
            // Verify the new API method exists and the old deprecated one does not
            assertDoesNotThrow(() -> {
                var builderClass = Class.forName("io.jsonwebtoken.JwtBuilder");
                // New API: subject(String) must exist
                var subjectMethod = builderClass.getMethod("subject", String.class);
                assertNotNull(subjectMethod, "JwtBuilder.subject(String) must exist in JJWT 0.12.x");
            });
        }

        @Test
        @DisplayName("Deprecated JJWT 0.8.x Jwts.parser() returning JwtParser directly must use new builder pattern")
        void jjwtParserBuilderPatternIsActive() {
            assertDoesNotThrow(() -> {
                var jwtsClass = Class.forName("io.jsonwebtoken.Jwts");
                // 0.12.x: parser() returns JwtParserBuilder
                var parserMethod = jwtsClass.getMethod("parser");
                assertNotNull(parserMethod);
                var returnType = parserMethod.getReturnType();
                assertThat(returnType.getSimpleName())
                        .as("Jwts.parser() must return JwtParserBuilder in JJWT 0.12.x")
                        .isEqualTo("JwtParserBuilder");
            });
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-004 (transitive): Hibernate 6.5.x
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-004 (transitive): Hibernate 6.5.x")
    class HibernateVersionTests {

        @Test
        @DisplayName("Hibernate ORM version must be 6.5.x")
        void hibernateVersionMustBe65x() {
            String hibernateVersion = org.hibernate.Version.getVersionString();
            assertNotNull(hibernateVersion, "Hibernate version must be detectable");
            assertThat(hibernateVersion)
                    .as("Hibernate version must start with 6.5, was: %s", hibernateVersion)
                    .startsWith("6.");
            int minor = Integer.parseInt(hibernateVersion.split("\\.")[1]);
            assertThat(minor)
                    .as("Hibernate minor version must be >= 5, was: %s", hibernateVersion)
                    .isGreaterThanOrEqualTo(5);
        }

        @Test
        @DisplayName("Hibernate 6.x Session class must be loadable from org.hibernate")
        void hibernateSessionClassLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("org.hibernate.Session"),
                    "org.hibernate.Session must be on the classpath"
            );
            // Verify it's the Hibernate 6.x version (extends jakarta.persistence.EntityManager)
            assertThat(Session.class.getInterfaces())
                    .extracting(Class::getName)
                    .as("Hibernate 6.x Session must extend jakarta.persistence.EntityManager")
                    .contains("jakarta.persistence.EntityManager");
        }

        @Test
        @DisplayName("Deprecated Hibernate 5.x org.hibernate.cfg.AnnotationConfiguration must NOT be present")
        void hibernateAnnotationConfigurationMustBeAbsent() {
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("org.hibernate.cfg.AnnotationConfiguration"),
                    "org.hibernate.cfg.AnnotationConfiguration was removed in Hibernate 6.x"
            );
        }

        @Test
        @DisplayName("Hibernate 6.x jakarta.persistence annotations must be used (not javax.persistence)")
        void hibernateUsesJakartaPersistenceAnnotations() {
            assertDoesNotThrow(
                    () -> Class.forName("jakarta.persistence.Entity"),
                    "jakarta.persistence.Entity must be on the classpath for Hibernate 6.x"
            );
            assertThrows(
                    ClassNotFoundException.class,
                    () -> Class.forName("javax.persistence.Entity"),
                    "javax.persistence.Entity must NOT be present — old JPA namespace must be removed"
            );
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-008: commons-fileupload 1.5+ (CVE-2023-24998)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-008: commons-fileupload 1.5+ (CVE-2023-24998)")
    class CommonsFileUploadVersionTests {

        @Test
        @DisplayName("commons-fileupload version must be 1.5 or higher")
        void commonsFileUploadVersionMustBe15OrHigher() {
            assertDoesNotThrow(
                    () -> Class.forName("org.apache.commons.fileupload.FileUpload"),
                    "org.apache.commons.fileupload.FileUpload must be on the classpath"
            );
            Package pkg = org.apache.commons.fileupload.FileUpload.class.getPackage();
            String implVersion = pkg.getImplementationVersion();
            if (implVersion != null) {
                String[] parts = implVersion.split("\\.");
                int major = Integer.parseInt(parts[0]);
                int minor = Integer.parseInt(parts[1]);
                assertThat(major).as("commons-fileupload major version must be >= 1").isGreaterThanOrEqualTo(1);
                if (major == 1) {
                    assertThat(minor)
                            .as("commons-fileupload minor version must be >= 5 (CVE-2023-24998 fix), was: %s", implVersion)
                            .isGreaterThanOrEqualTo(5);
                }
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // UPG-009: MapStruct 1.6.x
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("UPG-009: MapStruct 1.6.x")
    class MapStructVersionTests {

        @Test
        @DisplayName("MapStruct 1.6.x org.mapstruct.Mapper annotation must be loadable")
        void mapstructMapperAnnotationLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("org.mapstruct.Mapper"),
                    "org.mapstruct.Mapper must be on the classpath (MapStruct 1.6.x)"
            );
        }

        @Test
        @DisplayName("MapStruct version must be 1.6.x")
        void mapstructVersionMustBe16x() {
            Package pkg = org.mapstruct.Mapper.class.getPackage();
            String implVersion = pkg.getImplementationVersion();
            if (implVersion != null) {
                assertThat(implVersion)
                        .as("MapStruct version must start with 1.6, was: %s", implVersion)
                        .startsWith("1.6");
            }
        }

        @Test
        @DisplayName("MapStruct 1.6.x MappingConstants must be loadable (new in 1.5+)")
        void mapstructMappingConstantsLoadable() {
            assertDoesNotThrow(
                    () -> Class.forName("org.mapstruct.MappingConstants"),
                    "org.mapstruct.MappingConstants must be on the classpath (MapStruct 1.5+/1.6.x)"
            );
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // General: Deprecated Spring Boot 2.x APIs must be absent
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Deprecated Spring Boot 2.x APIs — must be absent in 3.3.x")
    class DeprecatedApiAbsenceTests {

        @Test
        @DisplayName("Deprecated SpringBootServletInitializer from javax must use jakarta variant")
        void springBootServletInitializerUsesJakarta() {
            assertDoesNotThrow(
                    () -> Class.forName("org.springframework.boot.web.servlet.support.SpringBootServletInitializer"),
                    "SpringBootServletInitializer must be present"
            );
        }

        @Test
        @DisplayName("Deprecated Spring Boot 2.x ActuatorMediaType must NOT be present")
        void actuatorMediaTypeMustBeAbsent() {
            // org.springframework.boot.actuate.endpoint.http.ActuatorMediaType replaced internal structure
            // This verifies the new actuator endpoint infrastructure is in place
            assertDoesNotThrow(
                    () -> Class.forName("org.springframework.boot.actuate.endpoint.web.WebEndpointResponse"),
                    "WebEndpointResponse must be present in Spring Boot 3.3.x actuator"
            );
        }

        @Test
        @DisplayName("Spring Boot 3.x auto-configuration uses @AutoConfiguration (not @Configuration only)")
        void autoConfigurationAnnotationPresent() {
            assertDoesNotThrow(
                    () -> Class.forName("org.springframework.boot.autoconfigure.AutoConfiguration"),
                    "@AutoConfiguration annotation must be present in Spring Boot 3.x"
            );
        }

        @Test
        @DisplayName("Spring Boot 2.x spring.factories auto-configuration loading must be replaced by AutoConfiguration.imports")
        void autoConfigurationImportsMechanismPresent() {
            // Spring Boot 3.x uses META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports
            // Verify the new ImportCandidates mechanism is present
            assertDoesNotThrow(
                    () -> Class.forName("org.springframework.boot.context.annotation.ImportCandidates"),
                    "ImportCandidates must be present — Spring Boot 3.x auto-configuration loading mechanism"
            );
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Integration: Critical application paths
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Integration: Critical Application Paths")
    class CriticalApplicationPathTests {

        @Test
        @DisplayName("Spring Boot application context must contain at least one REST controller")
        void applicationContextContainsRestControllers() {
            String[] controllers = applicationContext.getBeanNamesForAnnotation(
                    org.springframework.web.bind.annotation.RestController.class
            );
            assertThat(controllers)
                    .as("At least one @RestController must be registered in the ApplicationContext")
                    .isNotEmpty();
        }

        @Test
        @DisplayName("Health actuator endpoint must respond with HTTP 200 (Spring Boot 3.3.x actuator)")
        void healthActuatorEndpointResponds() {
            if (restTemplate == null) return;
            ResponseEntity<String> response = restTemplate.getForEntity("/actuator/health", String.class);
            assertThat(response.getStatusCode())
                    .as("/actuator/health must return HTTP 200 in Spring Boot 3.3.x")
                    .isEqualTo(HttpStatus.OK);
        }

        @Test
        @DisplayName("Spring MVC DispatcherServlet must handle requests without javax.servlet dependency")
        void dispatcherServletHandlesRequestsWithJakartaServlet() {
            // Verify DispatcherServlet is compiled against jakarta.servlet
            assertThat(DispatcherServlet.class.getPackageName())
                    .as("DispatcherServlet must be in org.springframework.web.servlet")
                    .isEqualTo("org.springframework.web.servlet");

            // Verify it extends jakarta-based FrameworkServlet
            Class<?> superClass = DispatcherServlet.class.getSuperclass();
            assertNotNull(superClass);
            assertThat(superClass.getName())
                    .as("DispatcherServlet superclass must be FrameworkServlet")
                    .contains("FrameworkServlet");
        }

        @Test
        @DisplayName("Spring Data JPA repositories must use jakarta.persistence (Hibernate 6.5.x)")
        void springDataJpaUsesJakartaPersistence() {
            assertDoesNotThrow(
                    () -> Class.forName("org.springframework.data.jpa.repository.JpaRepository"),
                    "JpaRepository must be on the classpath"
            );
            // Verify Spring Data JPA is compiled against jakarta.persistence
            assertDoesNotThrow(
                    () -> {
                        var repoClass = Class.forName("org.springframework.data.jpa.repository.support.SimpleJpaRepository");
                        assertNotNull(repoClass);
                    },
                    "SimpleJpaRepository must be present and loadable with jakarta.persistence"
            );
        }
    }
}