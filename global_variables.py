class ControlVariables:
    _variables = {
        "temp": 0,          # Temperature [degC]
        "heat": False,      # Heating on/off (on=1,off=0)
        "boil": False,      # Boiler on/off (on=1,off=0)
        "boil_mode": 0,     # Boiler mode (off=0,eco=1,hot=2,boost=3)
        "fan": 0,           # Ventilator (off=0,Stufe1=1 - Stufe10=10,Eco=11,High=13)
        "rst": False        # Error reset (if=1)
    }

    @classmethod
    def set_variable(cls, key, value):
        if key in cls._variables:
            cls._variables[key] = value
        else:
            raise KeyError(f"Invalid key: {key}")

    @classmethod
    def get_variable(cls, key):
        if key in cls._variables:
            return cls._variables[key]
        else:
            raise KeyError(f"Invalid key: {key}")

    @classmethod
    def get_all_variables(cls):
        return cls._variables.copy()
    

class LinVariables:
    _lin_message = bytearray(9)
    _lin_message_a = bytearray(200)
    _diag_message = None

    @classmethod
    def set_lin_message(cls, index, value):
        if 0 <= index < len(cls._lin_message):
            cls._lin_message[index] = value
        else:
            raise IndexError("Index out of range")

    @classmethod
    def get_lin_message(cls):
        return cls._lin_message

    @classmethod
    def set_lin_message_a(cls, index, value):
        if 0 <= index < len(cls._lin_message_a):
            cls._lin_message_a[index] = value
        else:
            raise IndexError("Index out of range")

    @classmethod
    def get_lin_message_a(cls):
        return cls._lin_message_a

    @classmethod
    def set_diag_message(cls, message):
        cls._diag_message = message

    @classmethod
    def get_diag_message(cls):
        return cls._diag_message

    @classmethod
    def set_entire_lin_message(cls, value):
        if isinstance(value, bytearray) and len(value) == len(cls._lin_message):
            cls._lin_message = value
        else:
            raise ValueError("Invalid value or length for lin_message")

    @classmethod
    def set_entire_lin_message_a(cls, value):
        if isinstance(value, bytearray) and len(value) == len(cls._lin_message_a):
            cls._lin_message_a = value
        else:
            raise ValueError("Invalid value or length for lin_message_a")