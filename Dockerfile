# Use Eclipse Temurin for OpenJDK with the specified version
FROM eclipse-temurin:21-jdk-alpine as build

# Set up a working directory
WORKDIR /app

# Copy the project files
COPY . .

# Build the project using Maven
RUN ./mvnw clean package -DskipTests

# Use a smaller runtime image for production
FROM eclipse-temurin:21-jre-alpine

# Create a user to run the application and a directory for the app
RUN addgroup -S spring && adduser -S spring -G spring
USER spring:spring

# Set up a working directory
WORKDIR /app

# Copy the JAR file from the build stage
COPY --from=build /app/target/*.jar app.jar

# Expose the application port
EXPOSE 8080

# Set the startup command
CMD ["java", "-jar", "app.jar"]

# Suggested additions for security practices
# HEALTHCHECK CMD curl --fail http://localhost:8080/actuator/health || exit 1