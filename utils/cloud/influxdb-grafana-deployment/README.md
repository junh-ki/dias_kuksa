To deploy pre-configured InfluxDB and Grafana containers with docker-compose.
You should run following commands before docker-compose

# 1. create a bridge network

$ docker network create monitor_network

# 2. create a volume for InfluxDB and Grafana

$ docker volume create influxdb-volume
$ docker volume create grafana-volume

# 3. When setting datasource for InfluxDB, Set HTTP/URL like following

$ http://influxdb:8086
