To deploy pre-configured InfluxDB and Grafana containers with docker-compose.
You should run following commands before docker-compose

# Prerequisites - docker, docker-compose

- docker <https://phoenixnap.com/kb/how-to-install-docker-on-ubuntu-18-04>

$ sudo groupadd docker
$ sudo usermod -aG docker $USER
- Re-Login or Restart the Server

- docker-compose
<https://docs.docker.com/compose/install/>
$ sudo curl -L "https://github.com/docker/compose/releases/download/1.27.4/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
$ sudo chmod +x /usr/local/bin/docker-compose
$ sudo ln -s /usr/local/bin/docker-compose /usr/bin/docker-compose
$ docker-compose --version

# 1. create a bridge network

$ docker network create monitor_network

# 2. create a volume for InfluxDB and Grafana

$ docker volume create influxdb-volume
$ docker volume create grafana-volume

# 3. Run Docker-compose (with the detached mode)

$ docker-compose up -d

# 4. When setting datasource for Grafana, Set HTTP/URL like following

$ http://influxdb:8086
