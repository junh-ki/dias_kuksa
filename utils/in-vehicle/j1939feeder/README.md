# SAE J1939 Reader for DBCFeeder in KUKSA.val

J1939Reader is to read CAN messages based on PGN (Parameter Group Number).
**It has already been merged to KUKSA.val** [J1939 Reader in KUKSA.val](https://github.com/eclipse/kuksa.val/blob/master/clients/feeder/dbc2val/j1939reader.py). To understand the concept and implementation, please refer to [DIAS Extension: SAE J1939 Option](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/j1939.html).

## Prerequisites

* Running `kuksa-val-server`. Please refer to [DIAS-KUKSA: KUKSA.val VSS Server Setup](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/invehicle.html#kuksa-val-kuksa-val-vss-server-setup) if you haven't built the KUKSA.val infrastructure yet.
* `j1939` and other relevant Python libraries
~~~
$ pip3 install j1939 python-can cantools serial websockets
$ git clone https://github.com/benkfra/j1939.git
$ cd j1939
$ pip install .
~~~
* A CAN interface, `can0` or `vcan0`. Please refer to [DIAS-KUKSA: CAN Interface for Hardware](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/hwsetup.html#can-interface-for-hardware).

## Step 1: Place the target J1939 DBC file in `kuksa.val/clients/feeder/dbc2val/`, the directory where `dbcfeeder.py` is located.

The J1939 DBC file should be provided by the observed vehicle's manufacturer. If it is not available, you can copy the entire string from [J1939 DBC Example](https://hackage.haskell.org/package/ecu-0.0.8/src/src/j1939_orig.dbc) and save it as `dbcfile.dbc` in the mentioned directory.

## Step 2: Place the mapping YML file in `kuksa.val/clients/feeder/dbc2val/`, the directory where `dbcfeeder.py` is located.

According to the JSON file you put into `kuksa-val-server`, create a mapping YML file in `kuksa.val/clients/feeder/dbc2val/`. An example mapping file can be found in `dias_kuksa/utils/in-vehicle/dbcfeeder_example_arguments/` [Link](https://github.com/junh-ki/dias_kuksa/blob/master/utils/in-vehicle/dbcfeeder_example_arguments/dias_mapping.yml).

## Step 3: Run `dbcfeeder.py` in the J1939 mode.

A few parameters need to be set for the script to run. Please make sure the following are set correctly:

* `--device`: Configured CAN Interface (Example: `--device can0` or `--device vcan0`)
* `--jwt`: Relative path to the JWT Security token file (Example: `--jwt ../../../certificates/jwt/super-admin.json.token`)
* `--dbc`: Name of the target J1939 DBC file (Example: `--dbc dbcfile.dbc`)
* `--mapping`: Name of the mapping YML file (Example: `--mapping mappingfile.yml`)
* `--j1939`: Enable SAE-J1939 Mode (Example: `--j1939`)

To start (Tested on Ubuntu 18.04 LTS), navigate to `kuksa.val/clients/feeder/dbc2val/`, the directory where `dbcfeeder.py` is located, and run:
~~~
$ python3 dbcfeeder.py --device vcan0 --jwt ../../../certificates/jwt/super-admin.json.token --dbc dbcfile.dbc --mapping mappingfile.yml --j1939
~~~
The above command follows the following format:
~~~
$ python3 dbcfeeder.py --device ${CAN-Interface-Name} --jwt ${Relative-JWT-JSON-Token-File-Directory} --dbc ${Relative-J1939-DBC-File-Directory} --mapping ${Relative-Mapping-YML-File-Directory} --j1939
~~~
