FROM eclipse-temurin:17-jdk-alpine as build

WORKDIR /app

# Copy the Maven project files
COPY pom.xml ./
COPY src ./src

# Cache the dependencies by downloading them only
RUN apk add --no-cache maven \
    && mvn dependency:go-offline

# Build the application
RUN mvn clean package -DskipTests

FROM eclipse-temurin:17-jre-alpine

WORKDIR /app

# Copy the Spring Boot jar from the build stage
COPY --from=build /app/target/*.jar app.jar

# Expose the default port for Spring Boot
EXPOSE 8080

# Run the app
CMD ["java", "-jar", "app.jar"]