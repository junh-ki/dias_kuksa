# Supplementary Files to run DBC Feeder

DBC Feeder is to read CAN frames that are being received from the target vehicle or a running log file, and decode them into signals. 

* In order to decode CAN frames into signals, a DBC file is required. A DBC file is expected to be handed over by the manufacturer of the observed vehicle.

* Once CAN frames are decoded into signals, only required ones are mapped to their corresponding paths in the in-vehicle GENIVI VSS server, `kuksa-val-server` [(Link)](https://github.com/eclipse/kuksa.val), with the help of `dias_mapping.yml`. If a decoded signal is listed in `dias_mapping.yml`, the signal is mapped to its corresponding stated path in `kuksa-val-server`.

Please refer to [DIAS-KUKSA: DBC Feeder](https://dias-kuksa-doc.readthedocs.io/en/latest/contents/invehicle.html#kuksa-val-dbcfeeder-py-setup) for more information.
