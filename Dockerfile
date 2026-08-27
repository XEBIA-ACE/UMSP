# Use exact versions for reproducibility
FROM maven:3.9.4-eclipse-temurin-11 AS build

# Set the working directory
WORKDIR /app

# Copy only the necessary files
COPY pom.xml ./
COPY src ./src

# Install dependencies and build the application
RUN mvn clean package -DskipTests

# Use a specific JRE for the application runtime
FROM eclipse-temurin:11-jre-alpine

# Set up the working directory in the final image
WORKDIR /app

# Copy the JAR file from the build stage
COPY --from=build /app/target/*.jar /app/app.jar

# Configure runtime environment for optimal Java execution
ENV JAVA_OPTS=""

# Expose application port
EXPOSE 8080

# Run the application
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar /app/app.jar"]