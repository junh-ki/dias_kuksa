# To add volume on your own influxdb image

# --- 1. Base Image --- 

FROM influxdb:1.8.3

# --- 2. Add volume ---
# relevant folders (data, meta, wal) from the local directory of `/var/lib/influxdb/`
# should already be placed in the directory where this Dockerfile is located.

ADD data /var/lib/influxdb/data/
ADD meta /var/lib/influxdb/meta/
ADD wal /var/lib/influxdb/wal/
