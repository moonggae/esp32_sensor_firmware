""" aioble_manager.py """
import aioble
import bluetooth
import json
import uasyncio as asyncio
import file_utils

_ENV_SERVICE_UUID = bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6937")
_ENV_SETTING_UUID = bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6938")
_ENV_UPDATE_UUID = bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6939")

_ADV_INTERVAL_US = 1_000_000 # 1sec
_ADV_DURATION_MS = 30 * 1000 # 30sec
_DEVICE_NAME = "NLTHSensor"

_BLE_CHUNK_SIZE = 5

class BLEManager:
    def __init__(self, rtc_manager):
        """Initialize BLEManager using aioble (GATT-based)"""
        self.rtc_manager = rtc_manager

        self._name = _DEVICE_NAME
        self.connected_device = None

        # Set up GATT services
        self._setup_gatt_services()
        print(f"BLE GATT Server Started with name: {self._name}")

    # ------------------------ [1. GATT Services and Advertising] ------------------------
    def _setup_gatt_services(self):
        """Set up BLE GATT services and characteristics"""
        self.service = aioble.Service(_ENV_SERVICE_UUID)

        # Device settings (Write)
        self.device_setting_char = aioble.BufferedCharacteristic(
            self.service,
            _ENV_SETTING_UUID,
            max_len=64,  
            write=True,
            capture = True,
        )

        # Temperature and humidity data service (Write & Notify)
        self.temp_humidity_char = aioble.BufferedCharacteristic(
            self.service,
            _ENV_UPDATE_UUID,
            max_len=64,
            indicate=True,
            write=True,
            notify = True,
            capture = True,
        )

        # Register GATT services
        aioble.register_services(self.service)
    
    async def advertise_for_setting(self):
        """Start BLE advertising (until registration and RTC sync are completed)"""
        while not all([self.rtc_manager.latest_time, self.rtc_manager.period]):
            print("Advertising BLE device for registration or RTC sync...")
            connection = await aioble.advertise(
                _ADV_INTERVAL_US,
                name=self._name,
                services=[self.service.uuid]
            )

            print(f"Connected to {connection.device}")
            self.connected_device = connection
            await self.handle_ble(connection)

        print("Device registered and RTC sync complete. BLE advertising stopped.")

    async def advertise_for_wakeup(self):
        """Start advertising for a forced wake-up scenario"""
        print(f"Advertising BLE device due to forced wake-up...")

        try:
            connection = await asyncio.wait_for(
                aioble.advertise(
                    _ADV_INTERVAL_US,
                    name=self._name,
                    services=[self.service.uuid]
                ),
                _ADV_DURATION_MS / 1000  # Convert timeout to seconds
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
                try:
                    # 둘 중 하나라도 데이터가 오면 처리
                    conn1, data1 = await asyncio.wait_for(self.device_setting_char.written(), 1)
                    if data1:
                        await self.process_device_settings(data1)
                except asyncio.TimeoutError:
                    pass

                try:
                    conn2, data2 = await asyncio.wait_for(self.temp_humidity_char.written(), 1)
                    if data2:
                        await self.send_data(data2)
                except asyncio.TimeoutError:
                    pass
                     
        except Exception as e:
            print(f"BLE Error: {e}")
            self.connected_device = None

    async def send_data(self, data):
        """Send CSV data in BLE_CHUNK_SIZE chunks"""
        try:
            settings = json.loads(data.decode())
            print(f"📥 Trigger Write Received: {settings}")

            if "timestamp" in settings:
                latest_time = int(settings["timestamp"])
                self.rtc_manager.set_rtc_datetime(latest_time) # Time sync
                print(f"⏰ RTC time updated via write trigger: {latest_time}")

            if not self.connected_device:
                print("No connected device to send CSV data.")
                return False

            structured_data = file_utils.read_csv_file()

            if not structured_data:
                await self.connected_device.notify(self.temp_humidity_char, json.dumps({"data": []}))
                print("No data to send, sent empty response.")
                return True

            total_batches = (len(structured_data) + _BLE_CHUNK_SIZE - 1) // _BLE_CHUNK_SIZE
            print(f"Sending {len(structured_data)} records via BLE in {total_batches} batches...")

            for i in range(0, len(structured_data), _BLE_CHUNK_SIZE):
                batch_data = structured_data[i:i + _BLE_CHUNK_SIZE]
                json_payload = json.dumps({"data": batch_data})

                try:
                    await self.temp_humidity_char.notify(self.connected_device, json_payload)
                    print(f"Sent batch {i // _BLE_CHUNK_SIZE + 1} / {total_batches}")
                except Exception as e:
                    print(f"❌ BLE send error (batch {i // _BLE_CHUNK_SIZE + 1}): {e}")
                    return False

                await asyncio.sleep(0.5)

            print("CSV Data sent successfully.")
            self.clear_sent_data()
            return True

        except OSError as e:
            print(f"File error: {e}")
            return False
    
    def clear_sent_data(self):
        """Clear CSV file after sending"""
        file_utils.clear_file()
        print("Sent data cleared, only header remains.")

    # ------------------------ [3. BLE Settings Modification] ------------------------
    async def process_device_settings(self, data):
        """Process Write Requests (Device Settings Update)"""
        try:
            settings = json.loads(data.decode())

            print(f"[PARSED JSON] {settings}")

            # Ensure required fields exist
            if not all(k in settings for k in ["timestamp", "period"]):
                print("Missing required fields in device settings.")
                return  # Stop processing if required values are missing

            latest_time = int(settings["timestamp"])  # ex) "1711360200" epoch(sec)
            period = int(settings["period"])   # ex) "3600" epoch(sec)

            # Save required values (RTC Memory & MAC Address)
            self.rtc_manager.set_rtc_datetime(latest_time) 
            self.rtc_manager.save_rtc_memory(latest_time, period) 

            print(f"Device settings updated: Time={latest_time}, Period={period}")

        except ValueError:
            print("JSON Parsing Error in Device Settings")

