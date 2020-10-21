# Production stage
FROM maven:3.6-jdk-11 AS build

# Copy the contents of the src directory
ADD src /usr/src/maven.consumer.hono/src/

# Copy the project file
COPY pom.xml /usr/src/maven.consumer.hono

# Copy the Dockerfile
COPY Dockerfile /usr/src/maven.consumer.hono

# Install dependencies
RUN apt-get update \
 && apt-get install mosquitto -y \
 && apt-get install mosquitto-clients -y

# Run maven
RUN mvn -f /usr/src/maven.consumer.hono/pom.xml package -DskipTests



FROM openjdk:11

WORKDIR /jardir

COPY --from=build /usr/src/maven.consumer.hono/target/maven.consumer.hono-0.0.1-SNAPSHOT.jar /jardir

ENTRYPOINT ["java", "-jar", "maven.consumer.hono-0.0.1-SNAPSHOT.jar"]

### docker build -t hono-influxdb-connector .
### docker run -p 8080:8080 -t hono-influxdb-connector --hono.client.tlsEnabled=true --hono.client.username=messaging@t20babfe7fb2840119f69e692f184127d --hono.client.password=s9VrzSsOQMzlSKFDgHrj --tenant.id=t20babfe7fb2840119f69e692f184127d
