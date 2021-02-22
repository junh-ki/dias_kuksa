# KUKSA.val Vehicle Data Preprocessing and Transmitting via MQTT with CloudFeeder and Preprocessor_Bosch

These scripts are to collect the required data from the in-vehicle server, `kuksa-val-server`, pre-process them, and transmit the result to the DIAS-KUKSA cloud.

Please refer to [DIAS-KUKSA: CloudFeeder Setup](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/invehicle.html#kuksa-val-cloudfeeder-py-setup) to set up an MQTT publisher in order to trasmit vehicle telemetry data to Bosch-IoT-Hub (Eclipse Hono).

## Prerequisites

Followings must be prepared:

* Mosquitto
~~~
$ sudo apt update
$ sudo apt install mosquitto mosquitto-clients
~~~
* A running Bosch-IoT-Hub instance: [DIAS-KUKSA: Bosch IoT Hub as Hono](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/cloud.html#bosch-iot-hub-as-hono)
* A running in-vehicle server, `kuksa-val-server`: [DIAS-KUKSA: Kuksa.val VSS Server Setup](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/invehicle.html#kuksa-val-kuksa-val-vss-server-setup)

## Step 1: Relocate the scripts (`cloudfeeder.py` and `preprocessor_bosch.py`)

These scripts need to be located in the same directory where `testclient.py` is also located: `kuksa.val/clients/vss-testclient/`

## Step 2: Make changes in `testclient.py`

At the end of the function, `def do_getValue(self, args)` add the following lines:
~~~
    datastore = json.loads(resp)
    return datastore
~~~

## Step 3: Download the server certificate file

The device endpoint certificate file can be downloaded [here](https://docs.bosch-iot-suite.com/hub/general-concepts/certificates.html).
Place the downloaded file in the same directory where `cloudfeeder.py` is located: `kuksa.val/clients/vss-testclient/`

## Step 4: Run `cloudfeeder.py`

A few parameters need to be set for the script to run. Please make sure the following are set correctly:

* `jwt`: JWT security token file, set as `--jwt ../../certificates/jwt/super-admin.json.token`
* `host`: MQTT Host URL, set as `--host mqtt.bosch-iot-hub.com`
* `port`: MQTT protocol's port number, set as `--port 8883`
* `username`: Credential authorization username of your Bosch-IoT-Hub instance, refer to [DIAS-KUKSA: Bosch IoT Hub as Hono](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/cloud.html#bosch-iot-hub-as-hono)
* `password`: Credential authorization password of your Bosch-IoT-Hub instance, refer to [DIAS-KUKSA: Bosch IoT Hub as Hono](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/cloud.html#bosch-iot-hub-as-hono)
* `cafile`: Name of the server certificate file downloaded in Step 3, set as `--cafile iothub.crt` 
* `type`: Data transmission type, set as `--type telemetry`
* `resume`: Resume the application with the accumulated data when restarting. If you want to continue with the data from the last execution, add the argument, `--resume`. Otherwise, ignore.

To start the script (Tested on Ubuntu 18.04 LTS), navigate to the directory, `kuksa.val/clients/vss-testclient/`, and run (in the resume mode):
~~~
$ python3 cloudfeeder.py --jwt ../../certificates/jwt/super-admin.json.token --host mqtt.bosch-iot-hub.com --port 8883 --username pc01@t20babfe7fb2840119f69e692f184127d --password kuksatutisfun01 --cafile iothub.crt --type telemetry --resume
~~~
The above command shall be changed according to the target Bosch-IoT-Hub instance's credential info and it should follow the following format (in the resume mode):
~~~
$ python3 cloudfeeder.py --jwt ${Relative-JWT-JSON-Token-File-Directory} --host ${MQTT-Host-URL} --port ${MQTT-Port-Number} --username ${Credential-Authorization-Username} --password ${Credential-Authorization-Password} --cafile ${Relative-Certificate-File-Directory} --type ${Data-Transmission-Type} --resume
~~~
