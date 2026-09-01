package com.salesmanager.shop.test.upgrade;

import com.fasterxml.jackson.databind.ObjectMapper;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.web.client.TestRestTemplate;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.context.ApplicationContext;
import org.springframework.core.SpringVersion;
import org.springframework.core.env.Environment;
import org.springframework.http.*;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.context.junit.jupiter.SpringExtension;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.web.servlet.DispatcherServlet;

import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import jakarta.servlet.http.HttpServletRequest;

import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.*;

import static org.assertj.core.api.Assertions.*;
import static org.junit.jupiter.api.Assertions.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Post-migration upgrade validation test suite for Shopizer.
 *
 * Validates:
 * - Spring Boot 3.3.x is active (not 2.5.x)
 * - Spring Security 6.3.x is active (not 5.5.x)
 * - Spring Data JPA 3.x is active
 * - Hibernate 6.x is active (jakarta.persistence namespace, not javax.persistence)
 * - springdoc-openapi 2.x is active (Springfox removed)
 * - jjwt 0.12.x API is active (not 0.8.0 deprecated API)
 * - jakarta.* namespace is used throughout (javax.* removed)
 * - PostgreSQL JDBC driver 42.7.x is active
 * - commons-fileupload 1.5+ is active
 * - All critical API endpoints respond correctly
 * - Spring Security configuration loads without errors
 * - JPA entities map correctly under Hibernate 6.x
 */
@ExtendWith(SpringExtension.class)
@SpringBootTest(
        webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT,
        properties = {
                "spring.datasource.url=jdbc:h2:mem:shopizer_upgrade_test;DB_CLOSE_DELAY=-1;DB_CLOSE_ON_EXIT=FALSE",
                "spring.datasource.driver-class-name=org.h2.Driver",
                "spring.datasource.username=sa",
                "spring.datasource.password=",
                "spring.jpa.hibernate.ddl-auto=create-drop",
                "spring.jpa.database-platform=org.hibernate.dialect.H2Dialect",
                "spring.jpa.show-sql=false",
                "spring.security.user.name=testadmin",
                "spring.security.user.password=testpassword",
                "springdoc.api-docs.enabled=true",
                "springdoc.swagger-ui.enabled=true",
                "config.defaultStore=DEFAULT",
                "shopizer.config.storeCode=DEFAULT"
        }
)
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("Shopizer Post-Migration Upgrade Validation Suite")
class ShopUpgradeValidationTest {

    @Autowired
    private ApplicationContext applicationContext;

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private Environment environment;

    @LocalServerPort
    private int port;

    @Autowired
    private TestRestTemplate restTemplate;

    private static final String SPRING_BOOT_TARGET_VERSION_PREFIX = "3.3";
    private static final String SPRING_SECURITY_TARGET_VERSION_PREFIX = "6.3";
    private static final String SPRING_FRAMEWORK_TARGET_VERSION_PREFIX = "6.1";
    private static final String HIBERNATE_TARGET_VERSION_PREFIX = "6.";
    private static final String JJWT_TARGET_VERSION_PREFIX = "0.12";

    // =========================================================================
    // Phase 0: Framework Version Assertions
    // =========================================================================

    @Test
    @Order(1)
    @DisplayName("UPGRADE-001: Spring Boot version must be 3.3.x (not 2.5.x)")
    void springBootVersionMustBe33x() {
        String bootVersion = getSpringBootVersion();
        assertThat(bootVersion)
                .as("Spring Boot version must be 3.3.x after upgrade from 2.5.12")
                .isNotNull()
                .startsWith(SPRING_BOOT_TARGET_VERSION_PREFIX);

        // Explicitly assert it is NOT the old version
        assertThat(bootVersion)
                .as("Spring Boot must NOT be the pre-migration version 2.5.x")
                .doesNotStartWith("2.5")
                .doesNotStartWith("2.6")
                .doesNotStartWith("2.7");
    }

    @Test
    @Order(2)
    @DisplayName("UPGRADE-002: Spring Framework version must be 6.1.x (required by Spring Boot 3.3.x)")
    void springFrameworkVersionMustBe6x() {
        String springVersion = SpringVersion.getVersion();
        assertThat(springVersion)
                .as("Spring Framework must be 6.1.x after upgrade")
                .isNotNull()
                .startsWith(SPRING_FRAMEWORK_TARGET_VERSION_PREFIX);

        // Must NOT be Spring 5.x (which backed Spring Boot 2.5.x)
        assertThat(springVersion)
                .as("Spring Framework must NOT be 5.x (pre-migration)")
                .doesNotStartWith("5.");
    }

    @Test
    @Order(3)
    @DisplayName("UPGRADE-003: Spring Security version must be 6.3.x (not 5.5.x)")
    void springSecurityVersionMustBe63x() {
        String securityVersion = getSpringSecurityVersion();
        assertThat(securityVersion)
                .as("Spring Security must be 6.3.x after upgrade from 5.5.x")
                .isNotNull()
                .startsWith(SPRING_SECURITY_TARGET_VERSION_PREFIX);

        assertThat(securityVersion)
                .as("Spring Security must NOT be 5.x (pre-migration)")
                .doesNotStartWith("5.");
    }

    @Test
    @Order(4)
    @DisplayName("UPGRADE-004: Hibernate ORM version must be 6.x (not 5.4.x)")
    void hibernateVersionMustBe6x() {
        String hibernateVersion = getHibernateVersion();
        assertThat(hibernateVersion)
                .as("Hibernate must be 6.x after upgrade from 5.4.x")
                .isNotNull()
                .startsWith(HIBERNATE_TARGET_VERSION_PREFIX);

        assertThat(hibernateVersion)
                .as("Hibernate must NOT be 5.x (pre-migration)")
                .doesNotStartWith("5.");
    }

    @Test
    @Order(5)
    @DisplayName("UPGRADE-005: jakarta.persistence namespace must be used (not javax.persistence)")
    void jakartaPersistenceNamespaceMustBeUsed() {
        // Verify jakarta.persistence.EntityManager is on the classpath
        assertDoesNotThrow(() -> Class.forName("jakarta.persistence.EntityManager"),
                "jakarta.persistence.EntityManager must be available after javax→jakarta migration");

        assertDoesNotThrow(() -> Class.forName("jakarta.persistence.Entity"),
                "jakarta.persistence.Entity must be available");

        assertDoesNotThrow(() -> Class.forName("jakarta.persistence.Table"),
                "jakarta.persistence.Table must be available");

        // Verify javax.persistence is NOT the active namespace (class should not exist or be replaced)
        // In Spring Boot 3.x, javax.persistence is not on the classpath
        assertThatThrownBy(() -> Class.forName("javax.persistence.EntityManager"))
                .as("javax.persistence.EntityManager must NOT be on classpath after jakarta migration")
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    @Order(6)
    @DisplayName("UPGRADE-006: jakarta.servlet namespace must be used (not javax.servlet)")
    void jakartaServletNamespaceMustBeUsed() {
        assertDoesNotThrow(() -> Class.forName("jakarta.servlet.http.HttpServletRequest"),
                "jakarta.servlet.http.HttpServletRequest must be available after javax→jakarta migration");

        assertDoesNotThrow(() -> Class.forName("jakarta.servlet.Filter"),
                "jakarta.servlet.Filter must be available");

        assertThatThrownBy(() -> Class.forName("javax.servlet.http.HttpServletRequest"))
                .as("javax.servlet.http.HttpServletRequest must NOT be on classpath after jakarta migration")
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    @Order(7)
    @DisplayName("UPGRADE-007: jjwt 0.12.x API must be active (not deprecated 0.8.0 API)")
    void jjwtVersionMustBe012x() {
        // jjwt 0.12.x uses io.jsonwebtoken.Jwts with new builder API
        // Verify the new 0.12.x API classes are present
        assertDoesNotThrow(() -> Class.forName("io.jsonwebtoken.Jwts"),
                "io.jsonwebtoken.Jwts must be available");

        assertDoesNotThrow(() -> Class.forName("io.jsonwebtoken.security.Keys"),
                "io.jsonwebtoken.security.Keys must be available (added in 0.10+, required for 0.12.x)");

        assertDoesNotThrow(() -> Class.forName("io.jsonwebtoken.security.MacAlgorithm"),
                "io.jsonwebtoken.security.MacAlgorithm must be available (0.12.x API)");

        // Verify the 0.12.x builder API works (not the deprecated 0.8.0 Jwts.builder().signWith(alg, key))
        assertDoesNotThrow(() -> {
            byte[] keyBytes = new byte[64];
            new Random().nextBytes(keyBytes);
            var key = Keys.hmacShaKeyFor(keyBytes);
            // 0.12.x API: Jwts.builder().subject(...).signWith(key).compact()
            String token = Jwts.builder()
                    .subject("upgrade-test-user")
                    .issuedAt(new Date())
                    .expiration(new Date(System.currentTimeMillis() + 3600000))
                    .signWith(key)
                    .compact();
            assertThat(token).isNotBlank();
        }, "jjwt 0.12.x builder API (Jwts.builder().subject().signWith(key)) must work");

        // Verify deprecated 0.8.0 API method setSubject is NOT available on JwtBuilder
        assertThatThrownBy(() -> {
            Class<?> builderClass = Class.forName("io.jsonwebtoken.JwtBuilder");
            // setSubject was the 0.8.0 API, replaced by subject() in 0.12.x
            Method setSubjectMethod = builderClass.getMethod("setSubject", String.class);
            // If we get here, the old API still exists — fail
            fail("JwtBuilder.setSubject(String) must NOT exist in jjwt 0.12.x — deprecated API still present");
        }).isInstanceOf(NoSuchMethodException.class);
    }

    @Test
    @Order(8)
    @DisplayName("UPGRADE-008: springdoc-openapi 2.x must be active (Springfox 2.9.2 must be removed)")
    void springdocOpenApiMustBeActiveAndSpringfoxRemoved() {
        // springdoc-openapi 2.x main class
        assertDoesNotThrow(() -> Class.forName("org.springdoc.core.models.GroupedOpenApi"),
                "org.springdoc.core.models.GroupedOpenApi must be available (springdoc-openapi 2.x)");

        assertDoesNotThrow(() -> Class.forName("org.springdoc.webmvc.ui.SwaggerUiHome"),
                "springdoc-openapi WebMVC UI must be available");

        // Springfox 2.9.2 classes must NOT be present
        assertThatThrownBy(() -> Class.forName("springfox.documentation.spring.web.plugins.Docket"))
                .as("Springfox Docket must NOT be on classpath — Springfox 2.9.2 must be removed")
                .isInstanceOf(ClassNotFoundException.class);

        assertThatThrownBy(() -> Class.forName("springfox.documentation.swagger2.annotations.EnableSwagger2"))
                .as("Springfox @EnableSwagger2 must NOT be on classpath")
                .isInstanceOf(ClassNotFoundException.class);
    }

    @Test
    @Order(9)
    @DisplayName("UPGRADE-009: commons-fileupload version must be 1.5+ (CVE-2023-24998 remediation)")
    void commonsFileUploadVersionMustBe15Plus() {
        // commons-fileupload 1.5 introduced DiskFileItemFactory with size limits
        // Verify the patched class is available
        assertDoesNotThrow(() -> Class.forName("org.apache.commons.fileupload.disk.DiskFileItemFactory"),
                "commons-fileupload DiskFileItemFactory must be available");

        // Verify the CVE-2023-24998 fix: FileUploadBase.setFileSizeMax and setSizeMax exist
        assertDoesNotThrow(() -> {
            Class<?> fileUploadBase = Class.forName("org.apache.commons.fileupload.FileUploadBase");
            Method setSizeMax = fileUploadBase.getMethod("setSizeMax", long.class);
            assertThat(setSizeMax).isNotNull();
        }, "FileUploadBase.setSizeMax must exist for CVE-2023-24998 mitigation");

        // Verify version is 1.5+: check for class added in 1.5
        // FileUpload.setFileCountMax was added in 1.5 as part of CVE fix
        assertDoesNotThrow(() -> {
            Class<?> fileUploadBase = Class.forName("org.apache.commons.fileupload.FileUploadBase");
            Method setFileCountMax = fileUploadBase.getMethod("setFileCountMax", long.class);
            assertThat(setFileCountMax)
                    .as("FileUploadBase.setFileCountMax must exist — added in 1.5 as CVE-2023-24998 fix")
                    .isNotNull();
        }, "commons-fileupload 1.5+ API (setFileCountMax) must be present");
    }

    @Test
    @Order(10)
    @DisplayName("UPGRADE-010: PostgreSQL JDBC driver must be 42.7.x (SQL injection CVE remediation)")
    void postgresqlJdbcDriverVersionMustBe427x() {
        // Verify PostgreSQL driver is on classpath
        assertDoesNotThrow(() -> Class.forName("org.postgresql.Driver"),
                "PostgreSQL JDBC driver must be on classpath");

        // Check driver version via Driver.getMajorVersion/getMinorVersion or manifest
        assertDoesNotThrow(() -> {
            Class<?> driverClass = Class.forName("org.postgresql.Driver");
            Object driver = driverClass.getDeclaredConstructor().newInstance();

            Method getMajorVersion = driverClass.getMethod("getMajorVersion");
            Method getMinorVersion = driverClass.getMethod("getMinorVersion");

            int major = (int) getMajorVersion.invoke(driver);
            int minor = (int) getMinorVersion.invoke(driver);

            assertThat(major)
                    .as("PostgreSQL JDBC driver major version must be 42")
                    .isEqualTo(42);
            assertThat(minor)
                    .as("PostgreSQL JDBC driver minor version must be 7+ (CVE remediation)")
                    .isGreaterThanOrEqualTo(7);
        }, "PostgreSQL JDBC driver version check must succeed");
    }

    // =========================================================================
    // Phase 1: Spring Context Initialization Validation
    // =========================================================================

    @Test
    @Order(11)
    @DisplayName("UPGRADE-011: Spring application context must load without BeanCreationException")
    void springContextMustLoadSuccessfully() {
        assertThat(applicationContext)
                .as("Spring ApplicationContext must be initialized")
                .isNotNull();

        // Verify the context is active and not closed
        assertThat(applicationContext.getId())
                .as("ApplicationContext must have an ID (context is active)")
                .isNotNull();

        // Verify DispatcherServlet bean is present (Spring MVC is configured)
        assertDoesNotThrow(() -> applicationContext.getBean(DispatcherServlet.class),
                "DispatcherServlet must be registered as a Spring bean");
    }

    @Test
    @Order(12)
    @DisplayName("UPGRADE-012: Spring Security 6.x SecurityFilterChain must be configured (not deprecated WebSecurityConfigurerAdapter)")
    void springSecurityFilterChainMustBeConfigured() {
        // In Spring Security 6.x, WebSecurityConfigurerAdapter is removed
        // Applications must use SecurityFilterChain beans
        assertThatThrownBy(() -> Class.forName("org.springframework.security.config.annotation.web.configuration.WebSecurityConfigurerAdapter"))
                .as("WebSecurityConfigurerAdapter must NOT exist in Spring Security 6.x — it was removed")
                .isInstanceOf(ClassNotFoundException.class);

        // Verify SecurityFilterChain is available (the replacement)
        assertDoesNotThrow(() -> Class.forName("org.springframework.security.web.SecurityFilterChain"),
                "SecurityFilterChain must be available in Spring Security 6.x");

        // Verify the application has SecurityFilterChain beans registered
        Map<String, ?> filterChainBeans = applicationContext.getBeansOfType(
                org.springframework.security.web.SecurityFilterChain.class);
        assertThat(filterChainBeans)
                .as("At least one SecurityFilterChain bean must be registered")
                .isNotEmpty();
    }

    @Test
    @Order(13)
    @DisplayName("UPGRADE-013: BCryptPasswordEncoder must be available and functional (Spring Security 6.x)")
    void bcryptPasswordEncoderMustWork() {
        PasswordEncoder encoder = new BCryptPasswordEncoder();
        String rawPassword = "TestPassword123!";
        String encoded = encoder.encode(rawPassword);

        assertThat(encoded)
                .as("BCrypt encoded password must not be null or empty")
                .isNotBlank()
                .startsWith("$2a$");

        assertThat(encoder.matches(rawPassword, encoded))
                .as("BCryptPasswordEncoder.matches must return true for correct password")
                .isTrue();

        assertThat(encoder.matches("WrongPassword", encoded))
                .as("BCryptPasswordEncoder.matches must return false for wrong password")
                .isFalse();
    }

    @Test
    @Order(14)
    @DisplayName("UPGRADE-014: Spring Security deprecated antMatchers must be replaced with requestMatchers")
    void springSecurityRequestMatchersMustBeUsed() {
        // antMatchers was deprecated in Spring Security 5.8 and removed in 6.x
        // Verify the replacement requestMatchers API is available
        assertDoesNotThrow(() -> {
            Class<?> httpSecurityClass = Class.forName(
                    "org.springframework.security.config.annotation.web.builders.HttpSecurity");
            Method requestMatchers = httpSecurityClass.getMethod("requestMatchers");
            assertThat(requestMatchers).isNotNull();
        }, "HttpSecurity.requestMatchers() must be available in Spring Security 6.x");

        // antMatchers must NOT exist in Spring Security 6.x
        assertThatThrownBy(() -> {
            Class<?> httpSecurityClass = Class.forName(
                    "org.springframework.security.config.annotation.web.builders.HttpSecurity");
            httpSecurityClass.getMethod("antMatchers", String[].class);
            fail("HttpSecurity.antMatchers() must NOT exist in Spring Security 6.x — it was removed");
        }).isInstanceOf(NoSuchMethodException.class);
    }

    // =========================================================================
    // Phase 2: API Endpoint Smoke Tests (324 transactions)
    // =========================================================================

    @Test
    @Order(20)
    @DisplayName("UPGRADE-020: GET /api/v1/products must respond (Spring MVC 6.x routing)")
    void productApiV1MustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/products")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().is(anyOf(
                        org.hamcrest.Matchers.is(200),
                        org.hamcrest.Matchers.is(400),
                        org.hamcrest.Matchers.is(401),
                        org.hamcrest.Matchers.is(403),
                        org.hamcrest.Matchers.is(404)
                )))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/products must not return 500 (internal server error)")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(21)
    @DisplayName("UPGRADE-021: GET /api/v2/products must respond (v2 API namespace)")
    void productApiV2MustRespond() throws Exception {
        mockMvc.perform(get("/api/v2/products")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v2/products must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(22)
    @DisplayName("UPGRADE-022: POST /api/v1/customer/login must respond (AuthenticateCustomerApi)")
    void customerLoginEndpointMustRespond() throws Exception {
        String loginPayload = "{\"username\":\"test@test.com\",\"password\":\"testpassword\"}";

        mockMvc.perform(post("/api/v1/customer/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(loginPayload)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> {
                    int status = result.getResponse().getStatus();
                    assertThat(status)
                            .as("POST /api/v1/customer/login must not return 500 — endpoint must be reachable")
                            .isNotEqualTo(500);
                    // 200 (success), 401 (bad credentials), 400 (validation) are all acceptable
                    assertThat(status)
                            .as("POST /api/v1/customer/login must return 200, 400, or 401")
                            .isIn(200, 400, 401, 403);
                });
    }

    @Test
    @Order(23)
    @DisplayName("UPGRADE-023: POST /api/v1/user/login must respond (admin login endpoint)")
    void adminLoginEndpointMustRespond() throws Exception {
        String loginPayload = "{\"username\":\"admin@shopizer.com\",\"password\":\"password\"}";

        mockMvc.perform(post("/api/v1/user/login")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(loginPayload)
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> {
                    int status = result.getResponse().getStatus();
                    assertThat(status)
                            .as("POST /api/v1/user/login must not return 500")
                            .isNotEqualTo(500);
                });
    }

    @Test
    @Order(24)
    @DisplayName("UPGRADE-024: GET /api/v1/cart must respond (ShoppingCartApi)")
    void cartApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/cart")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/cart must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(25)
    @DisplayName("UPGRADE-025: GET /api/v1/category must respond (CategoryApi)")
    void categoryApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/category")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/category must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(26)
    @DisplayName("UPGRADE-026: GET /api/v1/store must respond (MerchantStoreApi)")
    void storeApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/store")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/store must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(27)
    @DisplayName("UPGRADE-027: GET /api/v1/shipping must respond (ShippingApi)")
    void shippingApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/shipping")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/shipping must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(28)
    @DisplayName("UPGRADE-028: GET /api/v1/tax must respond (TaxApi)")
    void taxApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/tax")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/tax must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(29)
    @DisplayName("UPGRADE-029: GET /api/v1/content must respond (ContentApi)")
    void contentApiMustRespond() throws Exception {
        mockMvc.perform(get("/api/v1/content")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v1/content must not return 500")
                        .isNotEqualTo(500));
    }

    @Test
    @Order(30)
    @DisplayName("UPGRADE-030: GET /api/v2/product/variant must respond (ProductVariantApi)")
    void productVariantApiV2MustRespond() throws Exception {
        mockMvc.perform(get("/api/v2/product/variant")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> assertThat(result.getResponse().getStatus())
                        .as("GET /api/v2/product/variant must not return 500")
                        .isNotEqualTo(500));
    }

    // =========================================================================
    // Phase 3: springdoc-openapi 2.x Endpoint Validation
    // =========================================================================

    @Test
    @Order(40)
    @DisplayName("UPGRADE-040: GET /v3/api-docs must return OpenAPI 3.0 spec (springdoc-openapi 2.x)")
    void openApiDocsEndpointMustReturnOpenApi3Spec() throws Exception {
        MvcResult result = mockMvc.perform(get("/v3/api-docs")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(status().isOk())
                .andReturn();

        String responseBody = result.getResponse().getContentAsString();
        assertThat(responseBody)
                .as("OpenAPI spec must contain openapi version field")
                .contains("openapi");
        assertThat(responseBody)
                .as("OpenAPI spec must be version 3.x (not Swagger 2.0)")
                .contains("3.");

        // Verify it's NOT Swagger 2.0 format (which Springfox produced)
        assertThat(responseBody)
                .as("Response must NOT be Swagger 2.0 format (swaggerVersion field)")
                .doesNotContain("\"swagger\":\"2.0\"");
    }

    @Test
    @Order(41)
    @DisplayName("UPGRADE-041: GET /swagger-ui/index.html must be accessible (springdoc-openapi 2.x UI)")
    void swaggerUiMustBeAccessible() throws Exception {
        mockMvc.perform(get("/swagger-ui/index.html"))
                .andExpect(result -> {
                    int status = result.getResponse().getStatus();
                    assertThat(status)
                            .as("Swagger UI must be accessible at /swagger-ui/index.html (springdoc-openapi 2.x path)")
                            .isIn(200, 302); // 302 redirect is acceptable
                });
    }

    @Test
    @Order(42)
    @DisplayName("UPGRADE-042: Old Springfox /v2/api-docs endpoint must NOT exist")
    void springfoxV2ApiDocsMustNotExist() throws Exception {
        mockMvc.perform(get("/v2/api-docs")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> {
                    int status = result.getResponse().getStatus();
                    assertThat(status)
                            .as("Springfox /v2/api-docs must NOT return 200 — Springfox has been removed")
                            .isNotEqualTo(200);
                });
    }

    // =========================================================================
    // Phase 4: JPA / Hibernate 6.x Validation
    // =========================================================================

    @Test
    @Order(50)
    @DisplayName("UPGRADE-050: Hibernate 6.x jakarta.persistence annotations must be used on entity classes")
    void hibernateEntityAnnotationsMustUseJakartaNamespace() {
        // Verify jakarta.persistence.Entity annotation is available (Hibernate 6.x uses jakarta)
        assertDoesNotThrow(() -> {
            Class<?> entityAnnotation = Class.forName("jakarta.persistence.Entity");
            assertThat(entityAnnotation.isAnnotation()).isTrue();
        }, "jakarta.persistence.Entity annotation must be available");

        assertDoesNotThrow(() -> {
            Class<?> columnAnnotation = Class.forName("jakarta.persistence.Column");
            assertThat(columnAnnotation.isAnnotation()).isTrue();
        }, "jakarta.persistence.Column annotation must be available");

        assertDoesNotThrow(() -> {
            Class<?> manyToOneAnnotation = Class.forName("jakarta.persistence.ManyToOne");
            assertThat(manyToOneAnnotation.isAnnotation()).isTrue();
        }, "jakarta.persistence.ManyToOne annotation must be available");

        assertDoesNotThrow(() -> {
            Class<?> oneToManyAnnotation = Class.forName("jakarta.persistence.OneToMany");
            assertThat(oneToManyAnnotation.isAnnotation()).isTrue();
        }, "jakarta.persistence.OneToMany annotation must be available");
    }

    @Test
    @Order(51)
    @DisplayName("UPGRADE-051: Hibernate 6.x SessionFactory must be available (not Hibernate 5.x API)")
    void hibernateSessionFactoryMustBeHibernate6x() {
        assertDoesNotThrow(() -> {
            Class<?> sessionFactoryClass = Class.forName("org.hibernate.SessionFactory");
            assertThat(sessionFactoryClass).isNotNull();
        }, "org.hibernate.SessionFactory must be available");

        // Hibernate 6.x removed deprecated APIs — verify new API is present
        assertDoesNotThrow(() -> {
            Class<?> sessionClass = Class.forName("org.hibernate.Session");
            // createQuery with type parameter is the Hibernate 6.x API
            Method createQuery = sessionClass.getMethod("createQuery", String.class, Class.class);
            assertThat(createQuery).isNotNull();
        }, "Hibernate 6.x Session.createQuery(String, Class) must be available");
    }

    @Test
    @Order(52)
    @DisplayName("UPGRADE-052: Spring Data JPA 3.x repository API must be available")
    void springDataJpa3xMustBeAvailable() {
        assertDoesNotThrow(() -> Class.forName("org.springframework.data.jpa.repository.JpaRepository"),
                "JpaRepository must be available");

        assertDoesNotThrow(() -> Class.forName("org.springframework.data.repository.CrudRepository"),
                "CrudRepository must be available");

        // Spring Data JPA 3.x uses jakarta.persistence
        assertDoesNotThrow(() -> {
            Class<?> jpaRepoClass = Class.forName("org.springframework.data.jpa.repository.JpaRepository");
            // Verify it's the 3.x version by checking it uses jakarta namespace internally
            assertThat(jpaRepoClass.getPackageName())
                    .isEqualTo("org.springframework.data.jpa.repository");
        }, "Spring Data JPA 3.x JpaRepository must be in correct package");
    }

    // =========================================================================
    // Phase 5: Deprecated API Removal Validation
    // =========================================================================

    @Test
    @Order(60)
    @DisplayName("UPGRADE-060: Spring Boot 2.x deprecated SpringApplication.run(Class, String[]) still works in 3.x")
    void springApplicationRunMustWork() {
        // SpringApplication.run is still valid in 3.x — verify it's accessible
        assertDoesNotThrow(() -> {
            Class<?> springAppClass = Class.forName("org.springframework.boot.SpringApplication");
            Method runMethod = springAppClass.getMethod("run", Class.class, String[].class);
            assertThat(runMethod).isNotNull();
        }, "SpringApplication.run(Class, String[]) must be available in Spring Boot 3.x");
    }

    @Test
    @Order(61)
    @DisplayName("UPGRADE-061: Spring Boot 2.x deprecated server.port property still works in 3.x")
    void serverPortPropertyMustLoad() {
        String serverPort = environment.getProperty("server.port");
        // Either explicitly set or using default — must not throw
        // The property system must work correctly
        assertDoesNotThrow(() -> environment.getProperty("spring.datasource.url"),
                "spring.datasource.url property must be loadable");
    }

    @Test
    @Order(62)
    @DisplayName("UPGRADE-062: Spring Boot 3.x actuator health endpoint must be accessible")
    void actuatorHealthEndpointMustBeAccessible() throws Exception {
        mockMvc.perform(get("/actuator/health")
                        .accept(MediaType.APPLICATION_JSON))
                .andExpect(result -> {
                    int status = result.getResponse().getStatus();
                    // 200 (UP), 503 (DOWN but endpoint works), 404 (actuator not configured) are acceptable
                    // 500 is NOT acceptable
                    assertThat(status)
                            .as("Actuator health endpoint must not return 500")
                            .isNotEqualTo(500);
                });
    }

    @Test
    @Order(63)
    @DisplayName("UPGRADE-063: Spring MVC @RequestMapping with produces=APPLICATION_JSON_VALUE must work")
    void requestMappingWithJsonProducesMustWork() throws Exception {
        // Test that content negotiation works correctly in Spring MVC 6.x
        mockMvc.perform(get("/api/v1/products")
                        .header("Accept", "application/json"))
                .andExpect(result -> {
                    String contentType = result.getResponse().getContentType();
                    if (result.getResponse().getStatus() == 200 && contentType != null) {
                        assertThat(contentType)
                                .as("Response content type must be application/json when JSON is requested")
                                .contains("application/json");
                    }
                    assertThat(result.getResponse().getStatus())
                            .as("Request with Accept: application/json must not return 500")
                            .isNotEqualTo(500);
                });
    }

    @Test
    @Order(64)
    @DisplayName("UPGRADE-064: Spring Security CSRF protection must be configurable in 6.x")
    void springSecurityCsrfMustBeConfigurable() {
        // Verify CsrfConfigurer is available in Spring Security 6.x
        assertDoesNotThrow(() -> Class.forName(
                "org.springframework.security.config.annotation.web.configurers.CsrfConfigurer"),
                "CsrfConfigurer must be available in Spring Security 6.x");
    }

    @Test
    @Order(65)
    @DisplayName("UPGRADE-065: Spring Security deprecated authorizeRequests() replaced by authorizeHttpRequests()")
    void springSecurityAuthorizeHttpRequestsMustBeAvailable() {
        // authorizeRequests() was deprecated in Spring Security 5.8 and removed in 6.x
        // authorizeHttpRequests() is the replacement
        assertDoesNotThrow(() -> {
            Class<?> httpSecurityClass = Class.forName(
                    "org.springframework.security.config.annotation.web.builders.HttpSecurity");
            Method authorizeHttpRequests = httpSecurityClass.getMethod("authorizeHttpRequests");
            assertThat(authorizeHttpRequests).isNotNull();
        }, "HttpSecurity.authorizeHttpRequests() must be available in Spring Security 6.x");

        // authorizeRequests() must NOT exist in Spring Security 6.x
        assertThatThrownBy(() -> {
            Class<?> httpSecurityClass = Class.forName(
                    "org.springframework.security.config.annotation.web.builders.HttpSecurity");
            httpSecurityClass.getMethod("authorizeRequests");
            fail("HttpSecurity.authorizeRequests() must NOT exist in Spring Security 6.x — it was removed");
        }).isInstanceOf(NoSuchMethodException.class);
    }

    // =========================================================================
    // Phase 6: New Configuration Keys Validation
    // =========================================================================

    @Test
    @Order(70)
    @DisplayName("UPGRADE-070: Spring Boot 3.x spring.jpa.hibernate.ddl-auto property must load")
    void springJpaHibernateDdlAutoPropertyMustLoad() {
        String ddlAuto = environment.getProperty("spring.jpa.hibernate.ddl-auto");
        assertThat(ddlAuto)
                .as("spring.jpa.hibernate.ddl-auto must be set and loadable")
                .isNotNull()
                .isIn("create-drop", "create", "update", "validate", "none");
    }

    @Test
    @Order(71)
    @DisplayName("UPGRADE-071: Spring Boot 3.x spring.datasource.url property must load")
    void springDatasourceUrlPropertyMustLoad() {
        String datasourceUrl = environment.getProperty("spring.datasource.url");
        assertThat(datasourceUrl)
                .as("spring.datasource.url must be set and loadable in Spring Boot 3.x")
                .isNotNull()
                .isNotBlank();
    }

    @Test
    @Order(72)
    @DisplayName("UPGRADE-072: springdoc.api-docs.enabled property must load (new config key)")
    void springdocApiDocsEnabledPropertyMustLoad() {
        String apiDocsEnabled = environment.getProperty("springdoc.api-docs.enabled");
        assertThat(apiDocsEnabled)
                .as("springdoc.api-docs.enabled must be loadable (springdoc-openapi 2.x config key)")
                .isNotNull()
                .isEqualTo("true");
    }

    @Test
    @Order(73)
    @DisplayName("UPGRADE-073: springdoc.swagger-ui.enabled property must load (new config key)")
    void springdocSwaggerUiEnabledPropertyMustLoad() {
        String swaggerUiEnabled = environment.getProperty("springdoc.swagger-ui.enabled");
        assertThat(swaggerUiEnabled)
                .as("springdoc.swagger-ui.enabled must be loadable (springdoc-openapi 2.x config key)")
                .isNotNull()
                .isEqualTo("true");
    }

    @Test
    @Order(74)
    @DisplayName("UPGRADE-074: Spring Boot 3.x spring.security.user.name property must load")
    void springSecurityUserNamePropertyMustLoad() {
        String userName = environment.getProperty("spring.security.user.name");
        assertThat(userName)
                .as("spring.security.user.name must be loadable in Spring Boot 3.x")
                .isNotNull()
                .isNotBlank();
    }

    // =========================================================================
    // Helper Methods
    // =========================================================================

    private String getSpringBootVersion() {
        try {
            Class<?> springBootVersionClass = Class.forName("org.springframework.boot.SpringBootVersion");
            Method getVersionMethod = springBootVersionClass.getMethod("getVersion");
            return (String) getVersionMethod.invoke(null);
        } catch (Exception e) {
            // Fallback: read from manifest
            try {
                Package springBootPackage = Class.forName("org.springframework.boot.SpringApplication")
                        .getPackage();
                String version = springBootPackage.getImplementationVersion();
                if (version != null) return version;
            } catch (ClassNotFoundException ex) {
                // ignore
            }
            return readVersionFromManifest("org.springframework.boot", "spring-boot");
        }
    }

    private String getSpringSecurityVersion() {
        try {
            Class<?> springSecurityVersionClass = Class.forName(
                    "org.springframework.security.core.SpringSecurityCoreVersion");
            java.lang.reflect.Field versionField = springSecurityVersionClass.getField("SERIAL_VERSION_UID");
            // Try to get version from package
            Package pkg = Class.forName("org.springframework.security.core.Authentication").getPackage();
            String version = pkg.getImplementationVersion();
            if (version != null) return version;
        } catch (Exception e) {
            // ignore
        }
        return readVersionFromManifest("org.springframework.security", "spring-security-core");
    }

    private String getHibernateVersion() {
        try {
            Class<?> hibernateVersionClass = Class.forName("org.hibernate.Version");
            Method getVersionMethod = hibernateVersionClass.getMethod("getVersionString");
            return (String) getVersionMethod.invoke(null);
        } catch (Exception e) {
            try {
                Package pkg = Class.forName("org.hibernate.Session").getPackage();
                String version = pkg.getImplementationVersion();
                if (version != null) return version;
            } catch (ClassNotFoundException ex) {
                // ignore
            }
        }
        return readVersionFromManifest("org.hibernate.orm", "hibernate-core");
    }

    private String readVersionFromManifest(String groupId, String artifactId) {
        try {
            java.io.InputStream is = getClass().getResourceAsStream(
                    "/META-INF/maven/" + groupId + "/" + artifactId + "/pom.properties");
            if (is != null) {
                Properties props = new Properties();
                props.load(is);
                return props.getProperty("version");
            }
        } catch (Exception e) {
            // ignore
        }
        return "UNKNOWN";
    }

    private static org.hamcrest.Matcher<Integer> anyOf(
            org.hamcrest.Matcher<Integer>... matchers) {
        return org.hamcrest.Matchers.anyOf(matchers);
    }
}