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

# Run Docker-compose (with the detached mode)

$ docker-compose up -d
