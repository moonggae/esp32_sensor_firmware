""" aioble_manager.py """
import aioble
import bluetooth
import json
import uasyncio as asyncio
import config
import file_utils

class BLEManager:
    def __init__(self, rtc_manager):
        """Initialize BLEManager using aioble (GATT-based)"""
        self.rtc_manager = rtc_manager

        self._name = file_utils.load_text_from_file(config.NAME_FILE, default=config.DEVICE_NAME)
        self._registered_mac = file_utils.load_text_from_file(config.REGISTER_MAC_FILE, default=None)
        self.connected_device = None

        # Set up GATT services
        self._setup_gatt_services()
        print(f"BLE GATT Server Started with name: {self._name}")

    # ------------------------ [1. GATT Services and Advertising] ------------------------
    def _setup_gatt_services(self):
        """Set up BLE GATT services and characteristics"""
        self.service = aioble.Service(bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6937"))

        # Device settings (Write)
        self.device_setting_char = aioble.Characteristic(
            self.service, bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6938"), write=True
        )

        # Temperature and humidity data service (Read & Notify)
        self.temp_humidity_char = aioble.Characteristic(
            self.service, bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6939"), read=True, notify=True
        )

        # Register GATT services
        aioble.register_services(self.service)
    
    async def advertise(self):
        """Start BLE advertising (until registration and RTC sync are completed)"""
        while not all([self._registered_mac, self._rtc_manager.latest_time, self._rtc_manager.period]):
            print("Advertising BLE device for registration or RTC sync...")
            connection = await aioble.advertise(
                config.ADV_INTERVAL_MS,
                name=self._name,
                services=[self.service.uuid]
            )

            print(f"Connected to {connection.device}")
            self.connected_device = connection
            await self.handle_ble(connection)

        print("Device registered and RTC sync complete. BLE advertising stopped.")

    async def advertise_for_wakeup(self, timeout=60000):
        """Start advertising for a forced wake-up scenario"""
        print(f"Advertising BLE device for {timeout // 1000} seconds due to forced wake-up...")

        try:
            connection = await asyncio.wait_for(
                aioble.advertise(
                    config.ADV_INTERVAL_MS,
                    name=self._name,
                    services=[self.service.uuid]
                ),
                timeout / 1000  # Convert timeout to seconds
            )
            print(f"Connected to {connection.device}")
            self.connected_device = connection
            await self.handle_ble(connection)

        except asyncio.TimeoutError:
            print("No connection. Advertising timed out.")

    # ------------------------ [2. BLE Data Transmission] ------------------------
    async def handle_ble(self, connection):
        """Handle BLE Read/Notify Requests"""
        try:
            while connection.is_connected():
                # Handle device settings request (Write)
                device_settings = await self.device_setting_char.written()
                if device_settings:
                    await self.process_device_settings(device_settings)

                # Transmit CSV data only when a read request is received
                read_request = await self.temp_humidity_char.read()
                if read_request is not None:
                    print("Received Read Request for Temp/Humidity Data")
                    await self.send_csv_data()

                await asyncio.sleep(1)        
        except Exception as e:
            print(f"BLE Error: {e}")
            self.connected_device = None

    async def send_csv_data(self):
        """Send CSV data in BLE_CHUNK_SIZE chunks"""
        if not self.connected_device:
            print("No connected device to send CSV data.")
            return False

        try:
            with open(config.DATA_FILE, "r") as file:
                lines = [line.strip() for line in file.readlines()]

            data_lines = lines[1:] if len(lines) > 1 else []
            structured_data = [line.split(",") for line in data_lines]

            if not structured_data:
                await self.connected_device.notify(self.temp_humidity_char, json.dumps({"data": []}))
                print("No data to send, sent empty response.")
                return True

            total_batches = (len(structured_data) + config.BLE_CHUNK_SIZE - 1) // config.BLE_CHUNK_SIZE
            print(f"Sending {len(structured_data)} records via BLE in {total_batches} batches...")

            for i in range(0, len(structured_data), config.BLE_CHUNK_SIZE):
                batch_data = structured_data[i:i + config.BLE_CHUNK_SIZE]
                json_payload = json.dumps({"data": batch_data})

                try:
                    await self.connected_device.notify(self.temp_humidity_char, json_payload)
                    print(f"Sent batch {i // config.BLE_CHUNK_SIZE + 1} / {total_batches}")
                except Exception as e:
                    print(f"BLE send error: {e}")
                    return False

                await asyncio.sleep(0.3)

            print("CSV Data sent successfully.")
            self.clear_sent_data()
            return True

        except OSError as e:
            print(f"File error: {e}")
            return False
    
    def clear_sent_data(self):
        """Clear CSV file after sending"""
        file_utils.clear_file(config.DATA_FILE, config.DATA_HEADER)
        print("Sent data cleared, only header remains.")

    # ------------------------ [3. BLE Settings Modification] ------------------------
    async def process_device_settings(self, data):
        """Process Write Requests (Device Settings Update)"""
        try:
            settings = json.loads(data.decode())

            # Ensure required fields exist
            if not all(k in settings for k in ["latest_time", "period", "registered_mac"]):
                print("Missing required fields in device settings.")
                return  # Stop processing if required values are missing

            latest_time = settings["latest_time"]  # ex) "2025-03-19T15:30:00"
            period = settings["period"]  # ex) "01:00:00"
            registered_mac = settings["registered_mac"]

            # Save required values (RTC Memory & MAC Address)
            self.rtc_manager.set_rtc_datetime(latest_time) 
            self.rtc_manager.save_rtc_memory(latest_time, period) 
            file_utils.save_text_to_file(config.REGISTER_MAC_FILE, registered_mac)
            self._registered_mac = registered_mac

            # Process optional values (Device Name)
            if "name" in settings:
                name = settings["name"]
                file_utils.save_text_to_file(config.NAME_FILE, name)
                self._name = name
            else:
                name = self._name  # Keep existing name

            print(f"Device settings updated: Time={latest_time}, Period={period}, Name={name}, Mac={self._registered_mac}")

        except json.JSONDecodeError:
            print("JSON Parsing Error in Device Settings")

    # ------------------------ [4. BLE Scanning and Connection] ------------------------
    async def find_device(self):
        """Find devices through BLE scanning"""
        print("Scanning for BLE devices...")
        async with aioble.scan(5000, interval_us=30000, window_us=30000, active=True) as scanner:
            async for result in scanner:
                if result.device.addr_hex() == self._registered_mac:
                    print(f"Found registered device: {result.device.addr_hex()}")
                    return result.device

    async def connect_device(self, device):
        """Connect to a specific BLE device"""
        try:
            connection = await aioble.connect(device.address())
            print(f"Connected to {device.name()}")
            self.connected_device = connection
            return connection
        except Exception as e:
            print(f"Connection failed: {e}")
            return None
