"""
This script is to get the telemetry data that has been sent to the Hono 
dispatch router using AMQP 1.0 (North bound API) whenever the in-vehicle 
application sends the data to the protocol adapter. 
(then to the Hono dispatch router)

The script is intended not only to read but also store and make the data 
available for whatever purpose your use-case is aiming at.
For this, you want to connect to the north bound API using QPid Proton.
Therefore python-qpid-proton should be installed in advance:

$ pip install python-qpid-proton

In the later stage, this script shall be merged with an InfluxDB feeder
script that it plays a role of the connector between Hono and InfluxDB.

"""

import proton


