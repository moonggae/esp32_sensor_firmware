""" sensor_logger.py """
from machine import Pin, I2C
from bme import BME280
import file_utils

class SensorLogger:
    """Class to handle temperature, humidity, and material resistivity logging."""
    # ------------------------- Initialization -------------------------
    def __init__(self):
        # Initialize DHT20 (using I2C)
        self.i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        self.sensor = BME280(i2c=self.i2c)
        
        # Load existing data
        file_utils.create_csv_file()

    # ------------------------- Sensor Reading Methods -------------------------
    def get_sensor_data(self, current_time):
        """Read temperature & humidity from bme280 sensor."""
        try:
            temperature, humidity = self.sensor.values

            new_record = [current_time, temperature, humidity]
            file_utils.append_csv_file(new_record)
            print(f"Logged data: {new_record}")
            return temperature, humidity
        except Exception as e:
            print(f"Error reading sensor data: {e}")
            return None