# DIAS-KUKSA: Cloud

The detailed tutorial for the DIAS-KUKSA cloud can be found [here](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/cloud.html).

![DIAS-KUKSA: Cloud](../../images/dias-kuksa-cloud.png)

## Spring Boot applications for the DIAS-KUKSA cloud

As illustrated in the figure above, there are two Spring Boot applications that can be manually modified for the purpose of DIAS-KUKSA. Prior to deploying these applications, a `Bosch-IoT-Hub`, aka `Hono`, instance is expected to be up and running.

1. Hono-InfluxDB-Connector

`Hono-InfluxDB-Connector` is the application that connects `Bosch-IoT-Hub`, and `InfluxDB`. 
This can be found in `./maven.consumer.hono/`.

2. Diagnostics

`Diagnostics` is the application that evaluates data in `InfluxDB` at the end of the evaluation interval and stores the result data back in `InfluxDB` that are meant to be visualized in `Grafana`. 
This can be found in `./diagnostics/`.

## Docker Compose Deployment

Docker Compose is an automated deployment tool. In the context of the DIAS-KUKSA cloud, this includes open-source software including `InfluxDB` and `Grafana` as well as the Spring Boot applications introduced above. The Docker Compose script can be found in `./connector-influxdb-grafana-deployment/`.

## InfluxDB to Excel

`influxNOx2Excel.py` is a Python script that fetches accumulated data that are, or related to, `NOx`, from `InfluxDB`, and stores them in the excel sheet in chronological order after the evaluation interval ends. This can be found in the same directory, where this `README.md` file is located.
