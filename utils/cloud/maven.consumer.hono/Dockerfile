# Production stage
FROM maven:3.6-jdk-11 AS build

# Copy the source directory
COPY /src /app/src

# Copy the project file
COPY pom.xml /app

# Copy the Dockerfile
COPY Dockerfile /app

# Install dependencies
RUN apt-get update
RUN apt-get install mosquitto -y
RUN apt-get install mosquitto-clients -y

# Run maven
RUN mvn -f /app/pom.xml package -DskipTests




FROM openjdk:11

COPY --from=build /app/target/maven.consumer.hono-0.0.1-SNAPSHOT.jar app.jar

ENTRYPOINT ["java", "-jar", "maven.consumer.hono-0.0.1-SNAPSHOT.jar"]

### docker build -t hono-influxdb-connector .
