""" config.py """
import machine

# BLE Default Configuration
raw_uid = machine.unique_id()
DEVICE_UID = "".join("{:02X}".format(b) for b in raw_uid)  # Convert to HEX string
DEVICE_NAME = "Sensor" + DEVICE_UID[-4:]

# File paths for storing settings
NAME_FILE = "name.txt"
REGISTER_MAC_FILE = "mac.txt"
DATA_FILE = "data.csv"

# CSV file headers
DATA_HEADER = ["t", "tp", "hd"]

# BLE Advertising Configuration
# https://docs.micropython.org/en/latest/library/bluetooth.html#class-ble
# Advertising interval: Rounded to 625μs units, typically between 20ms (20000μs) and 10.24s (10240000μs)
ADV_INTERVAL_MS = 250_000
SCAN_INTERVAL = 30000
BLE_CHUNK_SIZE = 10  # Number of data rows sent per BLE transmission
