FROM maven:3.8.7-openjdk-21 AS builder
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN mvn clean package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=builder /app/target/my-app.jar my-app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "my-app.jar"]