# To add volume on your own influxdb image

# --- 1. Base Image --- 

FROM influxdb:1.8.3

# --- 2. Add volume ---
# relevant folder (influxdb) from the local directory of `/var/lib/`
# should already be placed in the directory where this Dockerfile is located.

ADD influxdb /var/lib/influxdb/

# ----- Docker Command Examples -----

# docker build -t mrki102/influxdb .
# docker run -p 8086:8086 -d -t mrki102/influxdb
# docker login --username={$USERNAME} --password={$PASSWORD}
# docker tag mrki102/influxdb mrki102/influxdb:1.0.0
# docker push mrki102/influxdb:1.0.0
# docker image rm image_id --force
# docker pull mrki102/influxdb:1.0.0
