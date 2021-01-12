# AMQP 1.0 North Bound Telemetry Consumer Application

***<ins>NOTE: This application is written based on [Example Consumer Application](https://github.com/bosch-io/iot-hub-examples) offered by Bosch.IO.</ins>***

This client app is to connect to the Hono interface's (or Bosch IoT Hub's) messaging endpoint and create a telemetry consumer that gets the telemetry data that has been sent to the Hono dispatch router by using AMQP 1.0 North Bound API whenever the in-vehicle application sends the data to the protocol adapter. (then to the Hono dispatch router)
The script is intended not only to read but also store and make the data available for whatever purpose your use-case is aiming at.

An existing IoT Hub (Hono) service instance and a valid tenant ID are needed to run the example application. Please refer to [Bosch IoT Hub - Getting Started](https://docs.bosch-iot-suite.com/hub/getting-started/prerequisites.html) to create a service instance.

## Prerequisites  

following software must be installed:

* curl ($ sudo apt-get install curl)
* Java (OpenJDK 11.0.8 is used here)
* Maven (Apache Maven 3.6.0 is used here)
* [mosquitto_sub](https://mosquitto.org/) for subscribing to receive commands

## Step 1: Build and Package

To build and package the application as a runnable JAR file run:

~~~
mvn clean package -DskipTests
~~~

## Step 2: Run Telemetry Consumer Application

The telemetry consumer application needs a few parameters set to run. Please make sure the following are set correctly:

* `messaging-username`: The username for the IoT Hub messaging endpoint (messaging@tenant-id)
* `messaging-password`: The password for the IoT Hub messaging endpoint
* `tenant-id`: The tenant ID (Default: t20babfe7fb2840119f69e692f184127d)
* `server-url`: The target InfluxDB URL address (Default: http://localhost:8086)
* `username`: InfluxDB username (Default: admin)
* `password`: InfluxDB password (Default: admin)
* `database`: The target database in InfluxDB (Default: dias_kuksa_tut)
* `eval-point`: THe evaluation point in time (Default: 50)

All the information needed for setting these parameters can be found in the 'Credentials' information of a IoT Hub service subscription information.

To start the example consumer application (Linux & Mac)

e.g) Navigate to the folder where this `README.md` file is located,
and run:
~~~
java -jar target/maven.consumer.hono-0.0.1-SNAPSHOT.jar --hono.client.tlsEnabled=true --hono.client.username=messaging@t20babfe7fb2840119f69e692f184127d --hono.client.password=s9VrzSsOQMzlSKFDgHrj --tenant.id=t20babfe7fb2840119f69e692f184127d --server.url=http://localhost:8086 --username=admin --password=admin --database=dias_kuksa_tut --eval.point=50
~~~
The above command shall be changed depending on the target service instance's credential info and it should follow the following format:
~~~
java -jar {Target jar file directory} --hono.client.tlsEnabled=true --hono.client.username=messaging@${HONO_TENANTID} --hono.client.password=${HONO_MESSAGINGPW} --tenant.id=${HONO_TENANTID} --server.url=${INFLUXDB_URL} --username=${INFLUXDB_USERNAME} --password=${INFLUXDB_PASSWORD} --database=${INFLUXDB_DATABASE} --eval.point=${EVALUATION_POINT}
~~~

The consumer application is ready as soon as 'Consumer ready' is printed on the console. The startup can take up to 10 seconds.
