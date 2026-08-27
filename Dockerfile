# Start a multi-stage build to minimize the final image size
# Stage 1: Build stage
FROM maven:3.8.6-openjdk-17-slim AS build

# Set the working directory
WORKDIR /app

# Copy the pom.xml and download dependencies only
COPY pom.xml .

# Download the dependencies in advance
RUN mvn dependency:go-offline

# Copy the project files and build the application
COPY src ./src
RUN mvn package -DskipTests

# Stage 2: Runtime stage
FROM eclipse-temurin:11-jre-alpine

# Set the working directory for the runtime
WORKDIR /app

# Copy the jar file from the build stage
COPY --from=build /app/target/*.jar app.jar

# Port on which the app will run
EXPOSE 8080

# Command to run the application
CMD ["java", "-jar", "app.jar"]