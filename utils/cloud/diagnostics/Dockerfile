# ----- 1. Jar Building Stage -----
FROM maven:3.6-jdk-11 AS build

# Copy the contents of the src directory
ADD src /usr/src/diagnostics/src/

# Copy the project file
COPY pom.xml /usr/src/diagnostics

# Copy the Dockerfile
COPY Dockerfile /usr/src/diagnostics

# Run maven
RUN mvn -f /usr/src/diagnostics/pom.xml package -DskipTests

# ----- 2. Image Building Stage -----
FROM openjdk:11

# Set the work directory
WORKDIR /jardir

# Copy the built jar file from the previous stage to the current directory 
COPY --from=build /usr/src/diagnostics/target/diagnostics-0.0.1-SNAPSHOT.jar /jardir

# Set the entry point
ENTRYPOINT ["java", "-jar", "diagnostics-0.0.1-SNAPSHOT.jar"]

# ----- Docker Command Examples -----

# docker build -t diagnostics .
# docker run -p 8080:8080 -t diagnostics --server.url=http://${CONNECTOR_EXPORTIP} --username=${INFLUXDB_USERNAME} --password=${INFLUXDB_PASSWORD} --database=dias_kuksa_tut --nox.map.mode=tscr_bad --eval.point=50
# docker login --username=${USERNAME} --password=${PASSWORD}
# docker tag diagnostics mrki102/diagnostics
# docker push mrki102/diagnostics
# docker image rm image_id --force
# docker pull mrki102/diagnostics
