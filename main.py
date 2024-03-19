import time
from decouple import config

from mqtt import connect_mqtt, publish, subscribe
from lin import trum_message, read_frame, trum_diagn_request
from global_variables import ControlVariables, LinVariables

DEBUG = config('DEBUG')

#Array of topics - Add, edit or remove to change topics to subscribe to
topics = [
    "truma_heating",
    "truma_boiler",
    "truma_temp",
    "truma_fan",
    "truma_reset"
]

client = None
t_room = None
t_water = None
status= None

def run():
    global status
    global t_room
    global t_water
    #connect to MQTT
    client = connect_mqtt()
    #Subscribe to Topics
    subscribe(client, topics)

    for i in range(20):
        client.loop()  # Get data from IO Broker and keep connection alive
        time.sleep(0.1)

    # Loop for diagnose frames
    print("[LIN] Reading data from device.")
    for ixx in range(3):
        # Output to Terminal
        if DEBUG:
            print("\nBlock {} ------------------------------------------------".format(ixx + 1))
            print("\nTime: {} ms\n".format(int(time.time() * 1000)))

        # Set truma mode (e.g. mode,temp,...)
        trum_message(ControlVariables.get_variable("temp"), ControlVariables.get_variable("heat"), ControlVariables.get_variable("boil"), ControlVariables.get_variable("boil_mode"), ControlVariables.get_variable("fan"))

        # Read data
        # Read ID=21
        read_frame(0x21)  # Status, ID=21, PID=61, Room temp, water temp,...
        t_room = float(LinVariables.get_lin_message_a()[1] + ((LinVariables.get_lin_message_a()[2] & 0x0F) << 8)) / 10 - 273  # Room temperature [degC]
        t_water = float((LinVariables.get_lin_message_a()[3] << 4) + ((LinVariables.get_lin_message_a()[2] & 0xF0) >> 4)) / 10 - 273  # Water temperature [degC]

        # Read ID=22
        read_frame(0x22)  # Status, ID=22, PID=E2, Mode(on,off), heating,...

        # Start Diagnosis
        trum_diagn_request(ixx, ControlVariables.get_all_variables())

        stat = [0xF0, 0x50, 0xD0, 0x70]

        # Status messages for IO Broker (MQTT)
        status_message = {
            0xF0: "Heating on",
            0x50: "Boiler on",
            0xD0: "Error",
            0x70: "Fatal error"
        }

        # Iterate through stat and check if the value matches any key in status_message
        for key, value in status_message.items():
            if LinVariables.get_lin_message_a()[1] == key:
                status = value
                break

    print("..done.")

    # Output to serial
    if DEBUG:
        print("\nRoom temp: {}".format(t_room))
        print("\nWater temp: {}".format(t_water))
        print("\nError message: {}\n".format(LinVariables.get_diag_message()))

    # Publish to IO Broker
    #Re-connect to MQTT
    client = connect_mqtt()
    publish(client, "Truma_TempRoom", str(t_room))
    publish(client, "Truma_TempWater", str(t_water))
    publish(client, "truma_diagMessage", str(LinVariables.get_diag_message()))
    publish(client, "truma_status", str(status))

    client.loop()
    time.sleep(0.5)



if __name__ == "__main__":
    run()