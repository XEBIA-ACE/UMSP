# Use the latest OpenJDK 11 base image with Alpine for reduced size
FROM eclipse-temurin:11-jre-alpine as builder

# Set the working directory
WORKDIR /app

# Copy the Maven build descriptor and source code
COPY pom.xml .
COPY src ./src

# Use Maven to build the application
RUN apk add --no-cache maven && \
    mvn clean package -DskipTests

# Use a JVM base image for runtime
FROM eclipse-temurin:11-jre-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the JAR file from the builder stage
COPY --from=builder /app/target/*.jar app.jar

# Expose the application port
EXPOSE 8080

# Command to run the application
CMD ["java", "-jar", "app.jar"]