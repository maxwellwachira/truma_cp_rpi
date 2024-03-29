# Truma CP with Raspberry Pi

## Prerequisites
- [Python3](https://www.python.org/)
- [RaspberryPi UART enabled](https://www.electronicwings.com/raspberry-pi/raspberry-pi-uart-communication-using-python-and-c#header2)
- UART to LIN BUS Converter


## Directory-Structure
    truma_cp_rpi  
	├── .env                     # Environment Variable 
    ├── .gitignore               # Git ignore file
    ├── control_variables.json   # A file that saves control variables in JSON format 
    ├── global_variables.py      # Contains two classes for managing global variables
    ├── lin.py                   # LIN BUS logic
    ├── main.py                  # Application entry point - main file
	├── mqtt.py                  # MQTT logic
    ├── README.md                # Readme file
    ├── requirements.txt		 # project dependencies
    ├── util.py		             # Utility functions to read and write JSON files

## Installation

1. clone the repository and navigate to the project directory

    ```bash
    git clone https://github.com/maxwellwachira/truma_cp_rpi.git
    ```
    ```bash
    cd truma_cp_rpi
    ```
2. Create a python virtual environment and activate it
    ```bash
    python3 -m venv venv
    ```
    ```bash
    source venv/bin/activate
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

### Connection
1. TX - GPIO14
2. RX - GPIO15

### Update .env

Update .env file with the correct environment Variables

### Running the Main Script

To run the main script, execute the following command:

```bash
python main.py
```


