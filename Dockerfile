FROM eclipse-temurin:21-jdk-alpine as builder

WORKDIR /app

# Copy the Maven project files
COPY pom.xml .

# Download all dependencies to enable easier build caching
RUN --mount=type=cache,target=/root/.m2 mvn dependency:go-offline

# Copy the project source
COPY src ./src

# Build the application
RUN --mount=type=cache,target=/root/.m2 mvn package -DskipTests

# Runtime image
FROM eclipse-temurin:21-jre-alpine

WORKDIR /app

# Copy the jar file from the builder stage
COPY --from=builder /app/target/*.jar app.jar

# Expose the application port
EXPOSE 8080

# Use a non-root user for better security if possible
USER 1000

# Set entrypoint to run the application
ENTRYPOINT ["java", "-jar", "app.jar"]