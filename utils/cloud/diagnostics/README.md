# Spring Boot InfluxDB-Diagnostics Application

This Spring Boot InfluxDB-Diagnostics application is to evaluate data stored in the connected InfluxDB server and produce diagnostic results that shall be displayed on the "DIAS-BOSCH: Evaluation" dashboard in Grafana.

## Prerequisites

Following software must be installed:

* Java (OpenJDK 11.0.8 is used here)
* Maven (Apache Maven 3.6.0 is used here)

## Step 1: Build and Package

To build and package the application as a runnable JAR file, navigate to `dias_kuksa/utils/cloud/diagnostics/` and run:

~~~
$ mvn clean package -DskipTests
~~~

## Step 2: Run InfluxDB-Diagnostics

The application needs a few parameters set to run. Please make sure the following are set correctly:

* `server.url`: Target InfluxDB URL address (Default: `--server.url=http://localhost:8086`)
* `username`: InfluxDB username (Default: `--username=admin`)
* `password`: InfluxDB password (Default: `--password=admin`)
* `database`: Target database in InfluxDB (Default: `--database=dias_kuksa_tut`)
* `nox.map.mode`: Target database in InfluxDB (choose one between: 'tscr_bad', 'tscr_intermediate', 'tscr_good', 'old_good', 'pems_cold', 'pems_hot') (Default: `--nox.map.mode=tscr_bad`)
* `eval.point`: Evaluation duration in seconds (Default: `--eval.point=350`)
* `pre.eval.disabled`: Whether to disable the pre-evaluation process or not (Default: `--pre.eval.disabled=false`)
* `modified.classifier`: Whether to use the modified classifier for evaluation or not (Default: `--modified.classifier=false`)
* `spring.config.location`: Relative directory of the properties file that includes the reference NOx map to load. In case the directory does not exist, it can be set as optional in which it proceeds with the default reference NOx map. (Example: `--spring.config.location=optional:./config/application.properties`) (In [`docker-compose.yml`](https://github.com/junh-ki/dias_kuksa/blob/master/utils/cloud/connector-influxdb-grafana-deployment/docker-compose.yml#L53), this is set to `--spring.config.location=optional:/config/config.properties`. Here, `/config/` is a Docker container's directory that is mounted by `/diagnostics_config/` from the local host. `/diagnostics_config/` can be found in the same directory where `docker-compose.yml` is located.)

To start the application (Tested on Ubuntu 18.04 LTS) **(Expected to be orchestrated with InfluxDB using Docker Compose)**
navigate to the folder where this `README.md` file is located and run:
~~~
$ java -jar target/diagnostics-0.0.1-SNAPSHOT.jar --server.url=http://localhost:8086 --username=admin --password=admin --database=dias_kuksa_tut --nox.map.mode=tscr_good --eval.point=50 --pre.eval.disabled=false --modified.classifier=false --spring.config.location=optional:./config/application.properties
~~~
The above command follows the following format:
~~~
$ java -jar ${Target-JAR-File-Directory} --server.url=${INFLUXDB_URL} --username=${INFLUXDB_USERNAME} --password=${INFLUXDB_PASSWORD} --database=${INFLUXDB_DATABASE} --nox.map.mode=${EVALUATION_TARGET} --eval.point=${EVALUATION_POINT} --pre.eval.disabled=${PRE_EVALUATION_DISABLED} --modified.classifier=${MODIFIED_CLASSIFIER} --spring.config.location=optional:./config/application.properties
~~~

The startup can take up to 10 seconds.
