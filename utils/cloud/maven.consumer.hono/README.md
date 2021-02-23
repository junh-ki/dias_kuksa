# AMQP 1.0 Spring Boot Hono-InfluxDB-Connector Application

***<ins>NOTE: This application is written based on [Example Consumer Application](https://github.com/bosch-io/iot-hub-examples) offered by Bosch.IO.</ins>***

This Spring Boot Hono-InfluxDB-Connector application is to connect to the Hono interface's (or Bosch IoT Hub's) messaging endpoint and receives telemetry message that are sent from the in-vehicle side to the Hono instance by using AMQP 1.0 North Bound API.
The application is intended not only to read telemetries but also process and store them in the InfluxDB server after connecting to it.

An existing IoT Hub (Hono) service instance and a valid tenant ID are needed to run the example application. Please refer to [DIAS-KUKSA: Bosch IoT Hub as Hono](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/cloud.html#bosch-iot-hub-as-hono) to create a service instance.

## Prerequisites

Following software must be installed:

* Java (OpenJDK 11.0.8 is used here)
* Maven (Apache Maven 3.6.0 is used here)
* [mosquitto_sub](https://mosquitto.org/) for subscribing the MQTT server to receive messages

## Step 1: Build and Package

To build and package the application as a runnable JAR file, navigate to `dias_kuksa/utils/cloud/maven.consumer.hono/` and run:

~~~
$ mvn clean package -DskipTests
~~~

## Step 2: Run Hono-InfluxDB-Connector

The application needs a few parameters that need to be set to run. Please make sure the following are set correctly:

* `hono.client.username`: The username for the IoT Hub messaging endpoint (Example Format: `messaging@t20babfe7fb2840119f69e692f184127d`)
* `hono.client.password`: The password for the IoT Hub messaging endpoint (Example Format: `s9VrzSsOQMzlSKFDgHrj`)
* `tenant.id`: The tenant ID (Example Format: `t20babfe7fb2840119f69e692f184127d`)
* `server.url`: The target InfluxDB URL address (Default: `http://localhost:8086`)
* `username`: InfluxDB username (Default: `admin`)
* `password`: InfluxDB password (Default: `admin`)
* `database`: The target database in InfluxDB (Default: `dias_kuksa_tut`)
* `eval.point`: THe evaluation duration in seconds (Default: `50`)

In regard to information of `hono.client.username`, `hono.client.password`, and `tenant.id` can be found in 'Show Credentials' in [Bosch-IoT-Suite Subscriptions](https://accounts.bosch-iot-suite.com/subscriptions/).

To start the application (Tested on Ubuntu 18.04 LTS) **(Expected to be orchestrated with InfluxDB using Docker Compose when a Bosch-IoT-Hub instance is running)**
navigate to the folder where this `README.md` file is located and run:
~~~
$ java -jar target/maven.consumer.hono-0.0.1-SNAPSHOT.jar --hono.client.tlsEnabled=true --hono.client.username=messaging@t20babfe7fb2840119f69e692f184127d --hono.client.password=s9VrzSsOQMzlSKFDgHrj --tenant.id=t20babfe7fb2840119f69e692f184127d --server.url=http://localhost:8086 --username=admin --password=admin --database=dias_kuksa_tut --eval.point=50
~~~
The above command shall be changed according to the target service instance's credential info and it should follow the following format:
~~~
$ java -jar ${Relative-Target-JAR-File-Directory} --hono.client.tlsEnabled=true --hono.client.username=messaging@${HONO_TENANTID} --hono.client.password=${HONO_MESSAGINGPW} --tenant.id=${HONO_TENANTID} --server.url=${INFLUXDB_URL} --username=${INFLUXDB_USERNAME} --password=${INFLUXDB_PASSWORD} --database=${INFLUXDB_DATABASE} --eval.point=${EVALUATION_POINT}
~~~

The consumer application is ready as soon as 'Consumer ready' is printed on the console. The startup can take up to 10 seconds.
