# Use the official Maven image for building the application
FROM maven:3.8.8-openjdk-11-slim AS build

WORKDIR /app

# Copy the Maven project files
COPY pom.xml .

# Download necessary dependencies into the Maven cache
RUN mvn dependency:go-offline

# Copy the entire project
COPY . .

# Build the application
RUN mvn package -DskipTests

# Use a minimal Java runtime for the application image
FROM eclipse-temurin:11-jre-slim

WORKDIR /app

# Copy the executable jar from the build stage
COPY --from=build /app/target/*.jar app.jar

# Expose the application port
EXPOSE 8080

# Run the application
ENTRYPOINT ["java", "-jar", "app.jar"]