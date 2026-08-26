FROM eclipse-temurin:17-jdk-alpine as builder

# Set the working directory inside the container
WORKDIR /app

# Copy the Maven project files into the container
COPY pom.xml ./
COPY src ./src

# Download necessary dependencies and build the project
RUN ./mvnw clean package -DskipTests

# Use a smaller base image for the runtime stage
FROM eclipse-temurin:17-jre-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the compiled application from the builder stage to the runtime stage
COPY --from=builder /app/target/*.jar app.jar

# Expose the application's listening port
EXPOSE 8080

# Run the application
CMD ["java", "-jar", "app.jar"]