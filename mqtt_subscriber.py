"""
* Hono & InfluxDB Connector *
(Intermediary Application between Hono & InfluxDB)
This is a test mqtt-subscriber script that reads a JSON string from 
a MQTT Broker (Eclipse Hono) that is originally sent by cloudfeeder.py 
and process the JSON string to be compliant with InfluxDB and send 
the result to InfluxDB.
(This should be located in-between Eclipse Hono and InfluxDB)
Refer to the following link:
https://stackoverflow.com/questions/32540670/is-mqtt-support-both-one-to-many-and-many-to-one

"""

import paho.mqtt.client as mqtt
import time
import json

def on_message(client, userdata, msg):
    topic=msg.topic
    m_decode=str(msg.payload.decode("utf-8","ignore"))
    print("data Received type",type(m_decode))
    print("data Received",m_decode)
    print("Converting from Json to Object")
    m_in=json.loads(m_decode)
    print(type(m_in))
    print("broker 2 address = ",m_in["broker2"])

# Subscribing the topic (should be aligned with the publisher)
topic = "test/json_test"
client = mqtt.Client("test_subscriber")
# on_message runs in a new thread
client.on_message=on_message
# Connecting to the MQTT broker (should be aligned with the publisher)
mqtt_broker = "test.mosquitto.org" # latency problem is outstanding...
print("Connecting to broker ", mqtt_broker)
client.connect(mqtt_broker)
client.loop_start()
time.sleep(3)

while True:
	print("Receiving data from the connected vehicle...")
	time.sleep(1)
	client.subscribe(topic)

client.loop_stop()
client.disconnect()
