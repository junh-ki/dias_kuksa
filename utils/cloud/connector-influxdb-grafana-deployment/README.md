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

# Set your email address in `grafana.ini` if you want to set the Grafana notification enabled

```
[smtp]
..
user = your@email.address
password = your_email_password # if you are using Gmail, you should have 2FA enabled and create an App password for this.
```

# Set the receiver's email address in ./grafana-provisioning/notifiers/notifier.yaml

```
notifiers:
    ..
    settings:
      addresses: receiver_1@email.address; receiver_2@email.address
```

# Set your Hono instance's information in docker-compose.yml

```
services:
   ..
   connector:
     ..
     command: --hono.client.tlsEnabled=true --hono.client.username=messaging@{$TENANT_ID} --hono.client.password={$MESSAGING_PW} --tenant.id={$TENANT_ID} --export.ip=influxdb:8086
```

# Run Docker Compose (with the detached mode)

$ docker-compose up -d

# Take down all the services in docker-compose.yml

$ docker-compose down

# Take down all volumes in docker-compose.yml

$ docker-compose down --volumes
