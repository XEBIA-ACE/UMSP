FROM eclipse-temurin:17-jdk-alpine AS builder

WORKDIR /build

COPY pom.xml .
COPY .mvn/ .mvn/
COPY mvnw .

RUN ./mvnw dependency:go-offline -B --no-transfer-progress

COPY . .

RUN ./mvnw clean package -B --no-transfer-progress -DskipTests \
    && mkdir -p target/extracted \
    && java -Djarmode=layertools -jar target/*.jar extract --destination target/extracted

FROM eclipse-temurin:17-jre-alpine AS runtime

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

WORKDIR /app

COPY --from=builder --chown=appuser:appgroup /build/target/extracted/dependencies/ ./
COPY --from=builder --chown=appuser:appgroup /build/target/extracted/spring-boot-loader/ ./
COPY --from=builder --chown=appuser:appgroup /build/target/extracted/snapshot-dependencies/ ./
COPY --from=builder --chown=appuser:appgroup /build/target/extracted/application/ ./

USER appuser

EXPOSE 8080

ENTRYPOINT ["java", \
    "-XX:+UseContainerSupport", \
    "-XX:MaxRAMPercentage=75.0", \
    "-Djava.security.egd=file:/dev/./urandom", \
    "org.springframework.boot.loader.launch.JarLauncher"]