# Use the latest long-term supported (LTS) version suitable for Java 17
FROM eclipse-temurin:17-jdk-alpine as builder

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Use Maven to compile and package the application
RUN mvn clean package -DskipTests

# Second stage to create a minimal runtime image
FROM eclipse-temurin:17-jre-alpine

# Set working directory
WORKDIR /app

# Copy the packaged application from the builder stage
COPY --from=builder /app/target/*.jar /app/application.jar

# Expose the application port
EXPOSE 8080

# Command to run the application
CMD ["java", "-jar", "/app/application.jar"]