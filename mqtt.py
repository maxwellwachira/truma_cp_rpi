import random
import time

from paho.mqtt import client as mqtt_client
from typing import List, Dict, Any
from decouple import config

from util import update_json, read_json, update_dict
from global_variables import ControlVariables

#get MQTT environment variables
MQTT_BROKER = config('MQTT_BROKER')
MQTT_USER = config('MQTT_USER')
MQTT_PASSWORD = config('MQTT_PASSWORD')
MQTT_PORT = config('MQTT_PORT')

#get if debug mode is True
DEBUG = config('DEBUG')

#Control Variable .json filename
FILENAME = config('FILENAME')

#client ID
client_id = f'truma-heater-client-{random.randint(0, 1000)}'


#connect to mqtt broker and returns a connection instance.
def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            if DEBUG:
                print("Connected to MQTT Broker!")
        else:
            if DEBUG:
                print("Failed to connect, return code %d\n", rc)

            #update control variables with last stored values
            json_file = read_json(FILENAME)
            update_dict(json_file)
    
    client = mqtt_client.Client(client_id)
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)
    client.on_connect = on_connect
    client.connect(MQTT_BROKER, int(MQTT_PORT))
    return client


#subscribe to topics
def subscribe(client: mqtt_client, topics: List[str]):
    def on_message(client, userdata, msg):
        if DEBUG:
            print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
        if msg.topic == "truma_heating":
            ControlVariables.set_variable("heat", msg.payload.decode() == "ON")
        elif msg.topic == "truma_boiler":
            boilMode = int(msg.payload.decode())
            ControlVariables.set_variable("boil", boilMode > 0)
        elif msg.topic == "truma_temp":
            ControlVariables.set_variable("temp", int(msg.payload.decode()))
        elif msg.topic == "truma_fan":
            ControlVariables.set_variable("fan", int(msg.payload.decode()))
        elif msg.topic == "truma_reset":
            ControlVariables.set_variable("rst", msg.payload.decode() == "ON")

        #update control variables
        update_json(FILENAME, ControlVariables.get_all_variables)

    # Subscribe to each topic in the list
    for topic in topics:
        client.subscribe(topic)

    client.on_message = on_message



def publish(client: mqtt_client, topic: str, msg: Any):
    time.sleep(1)
    result = client.publish(topic, msg)
    # result: [0, 1]
    status = result[0]
    if status == 0:
        if DEBUG:
            print(f"Send `{msg}` to topic `{topic}`")
    else:
        if DEBUG:
            print(f"Failed to send message to topic {topic}")
     