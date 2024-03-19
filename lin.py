import time

from serial import Serial
from decouple import config

from global_variables import LinVariables

DEBUG = config('DEBUG')

line_serial_speed = 9600 #baudrate
break_duration = 200  # Replace 200 with your desired break duration in milliseconds


#Temperature code [degC] 5-30 (0-4)=0xAA=off
temp_hex = [0xAA, 0xAA, 0xAA, 0xAA, 0xAA, 0xDC, 0xE6, 0xF0, 0xFA, 0x04, 0x0E, 0x18, 0x22, 0x2C, 0x36, 0x40, 0x4A, 0x54, 0x5E, 0x68, 0x72, 0x7C, 0x86, 0x90, 0x9A, 0xA4, 0xAE, 0xB8, 0xC2, 0xCC, 0xD6]


lin_serial = Serial('/dev/ttyUSB0', line_serial_speed)

#Generate Break signal LOW on LIN bus
def serial_break():
    global lin_serial  # Declare lin_serial as global
    if lin_serial.is_open:
        lin_serial.close()
    lin_serial = Serial('/dev/ttyUSB0', line_serial_speed)
    lin_serial.dtr = False  # send break
    time.sleep(break_duration / 1000)  # duration break time in seconds
    lin_serial.dtr = True
    time.sleep(1 / line_serial_speed)  # wait 1 bit
    
#Checksum
def lin_checksum(n_byte, ck_mode):
    lin_message = LinVariables.get_lin_message()
    if ck_mode == "enhanced":
        sum_value = sum(lin_message[:n_byte])
        while sum_value >> 8:
            sum_value = (sum_value & 255) + (sum_value >> 8)
        return (~sum_value) & 0xFF
    else:
        sum_value = sum(lin_message[:n_byte-1])
        while sum_value >> 8:
            sum_value = (sum_value & 255) + (sum_value >> 8)
        return (~sum_value) & 0xFF
    
# ID Parity
def add_id_parity(lin_id):
    p0 = (lin_id & 0b0001) ^ ((lin_id & 0b0010) >> 1) ^ ((lin_id & 0b0100) >> 2) ^ ((lin_id & 0b10000) >> 4)
    p1 = ~(((lin_id & 0b0010) >> 1) ^ ((lin_id & 0b01000) >> 3) ^ ((lin_id & 0b10000) >> 4) ^ ((lin_id & 0b100000) >> 5)) & 0b1
    return ((p0 | (p1 << 1)) << 6)

#Control function
def trum_message(temp, heat, boil, boil_mode, fan):
    h = 0x0A  # Heating on/off
    b = 0xA0  # Boiler on/off

    LinVariables.set_lin_message(0, 0x20)  # Frame identifier (20-PID)

    # Heating
    if heat:
        h = 0x0B  # Heating on
        LinVariables.set_lin_message(1, temp_hex[temp])  # Selected Temp (AA-Off, DC-5, E6-6, F0-7,... degC | Fahrenheit*10)
    else:
        h = 0x0A  # Heating off
        LinVariables.set_lin_message(1, 0xAA)  # Temperature off (0xAA)

    # Set boiler
    if boil:
        b = 0x20  # Boiler on
    else:
        b = 0xA0  # Boiler off
        LinVariables.set_lin_message(3, 0xAA)  # Boiler mode off

    LinVariables.set_lin_message(2, b + h)  # Heater and Boiler mode (combined Byte)

    if boil:
        # Boiler mode (AA-off, C3-eco, D0- Hot+Boost)
        if boil_mode == 1:
            LinVariables.set_lin_message(3, 0xC3)  # Boiler eco
        elif boil_mode == 2:
            LinVariables.set_lin_message(3, 0xD0)  # Boiler hot
        elif boil_mode == 3:
            LinVariables.set_lin_message(1, 0xAA)  # Temp off (necessary for Boost)
            LinVariables.set_lin_message(2, 0x2A)  # Heating off + Boiler on (necessary for Boost)
            LinVariables.set_lin_message(3, 0xD0)  # Boiler boost

    LinVariables.set_lin_message(4, 0xFA)  # Energiemix (FA-Gas+Mix,00-Elektro)
    LinVariables.set_lin_message(5, 0x00)  # Mode (00-Gas,09-Mix/Elektro1,12-Mix/Elektro2)

    # Ventilator
    if heat and (fan < 11):
        LinVariables.set_lin_message(6, 16 * 11 + 0x01)  # Avoid fan to be in level 1-10 or off when heating on
    elif not heat and boil:
        LinVariables.set_lin_message(6, 0x01)  # Turn off fan when only boiler (no heating) is set active
    else:
        LinVariables.set_lin_message(6, 16 * fan + 0x01)  # Model (X1 - Gas  X2 - Elektro  X3 - Mix  BX - Lüfter Eco DX - Lüfter High  1X - vent 1 2X - Vent 2 3X - Vent 3 4X - Vent 4 5X - Vent 5 6X - Vent 6 7X - Vent 7 8X - Vent 8 9X - Vent 9 AX - Vent 10)

    LinVariables.set_lin_message(7, 0xE0)  # Unknown (E0)
    LinVariables.set_lin_message(8, 0x0F)  # Unknown (0F)

    cksum = lin_checksum(9, "enhanced")
    # cksum = lin_checksum(9, "classic")

    serial_break()
    lin_serial.write(b'\x55')  # Sync
    lin_serial.write(LinVariables.get_lin_message())  # Message (array from 1..8) // Original
    lin_serial.write(bytes([cksum]))
    lin_serial.flush()

    if DEBUG:
        print("ID: 20 --> PID: 20")
        print("lin_message:", LinVariables.get_lin_message().hex())
        print(" - Checksum:", hex(cksum))

#Read answer from Lin bus
def read_frame(m_id):

    # Clear lin_message_a (set values to zero)
    LinVariables.set_entire_lin_message_a(bytearray(200))

    ix = 0
    lin_id = (m_id & 0x3F) | add_id_parity(m_id)

    time.sleep(0.04)  # Wait 40µs
    serial_break()  
    lin_serial.write(b'\x55')
    lin_serial.write(bytes([lin_id]))  
    lin_serial.flush()
    time.sleep(0.4)

    if lin_serial.in_waiting:
        # Read serial
        while lin_serial.in_waiting:
            LinVariables.set_lin_message_a(ix, ord(lin_serial.read()))
            ix += 1
            if ix > 9:
                break

    if DEBUG:
        print("\nID: {:02X} --> PID: {:02X}".format(lin_id, m_id))
        print("lin_message_a:",  LinVariables.get_lin_message_a().hex())

# Diagnosis
def trum_diagn_request(ixx, control_vars):

    if ixx == 0:
        lin_message = bytearray([0x3C, 0x01, 0x06, 0xB8, 0x40, 0x03, 0x01 if control_vars["heat"] or control_vars["boil"] or (control_vars["fan"] > 0) else 0x00, 0x00, 0xFF])
    elif ixx == 1:
        lin_message = bytearray([0x3C, 0x7F, 0x06, 0xB2, 0x00, 0x17, 0x46, 0x40, 0x03])
    elif ixx == 2:
        lin_message = bytearray([0x3C, 0x7F, 0x06, 0xB2, 0x23, 0x17, 0x46, 0x40, 0x03])

    LinVariables.set_entire_lin_message(lin_message)

    cksum = lin_checksum(9, "classic")

    serial_break()
    lin_serial.write(b'\x55')  # Sync
    lin_serial.write(lin_message)  # Message (array from 1..8) // Original
    lin_serial.write(bytes([cksum]))
    lin_serial.flush()

    if DEBUG:
        print("\nID: 3C --> PID: 3C")
        print("LinMessage:", LinVariables.get_lin_message().hex())
        print(" - Checksum:", hex(cksum))

    # Evaluate answer
    read_frame(0x3D)  # Read diagnostic answer

    # Error messages for IO Broker (MQTT)
    err_message = [
        "E517H - with reset",
        "E517H - with reset",
        "E517H",
        "E517H - reset unknown",
        "-",
        "W255H",
        "W255H",
    ]  # Error messages

    # LIN error messages
    err = [
        bytearray([0x7d, 0x01, 0x06, 0xF2, 0x02, 0x05, 0x11, 0xCA, 0x0A]),  # E517H - Gas empty
        bytearray([0x7d, 0x01, 0x06, 0xF2, 0x02, 0x05, 0x11, 0x2D, 0x0C]),  # E517H - Gas empty
        bytearray([0x7d, 0x01, 0x06, 0xF2, 0x02, 0x05, 0x11, 0xE5, 0x0C]),  # E517H - Gas empty
        bytearray([0x7d, 0x01, 0x06, 0xF2, 0x02, 0x05, 0x11, 0x1A, 0x0C]),  # E517H - Gas empty
        bytearray([0x7d, 0x01, 0x06, 0xF2, 0x02, 0x00, 0x00, 0x00, 0x00]),  # Normal - normal operating mode
        bytearray([0x7d, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),  # W255H - no connection between devices (no Lin answer)
        bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),  # W255H - no connection between devices (no Lin answer)
    ]

    if ixx == 2:
        for i in range(len(err)):
            if LinVariables.get_lin_message_a() == err[i]:
                LinVariables.set_diag_message(err_message[i])
                break



