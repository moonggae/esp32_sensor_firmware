import aioble
import bluetooth
import uasyncio as asyncio
import json

# BLE UUIDs
_SERVICE_UUID = bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6937")
_NOTIFY_UUID = bluetooth.UUID("5f97247b-4474-424c-a826-f8ec299b6939")

# Advertising Settings
_ADV_INTERVAL_US = 1_000_000  # 1 second
_DEVICE_NAME = "TestBLE"
_BLE_CHUNK_SIZE = 5  # Number of records per batch
_TOTAL_BATCHES = 3  # Total 15 records to be sent

class TestBLEServer:
    def __init__(self):
        self.connected_device = None
        self._setup_gatt_services()

    def _setup_gatt_services(self):
        """Set up BLE GATT services and characteristics"""
        self.service = aioble.Service(_SERVICE_UUID)
        
        self.notify_char = aioble.BufferedCharacteristic(
            self.service,
            _NOTIFY_UUID,
            max_len=64,
            write=True,
            notify=True,
            capture=True,
        )
        
        aioble.register_services(self.service)
        print("✅ BLE GATT Server Initialized")

    async def advertise(self):
        """Advertise and wait for a connection"""
        while True:
            print("📢 Advertising...")
            connection = await aioble.advertise(
                _ADV_INTERVAL_US,
                name=_DEVICE_NAME,
                services=[self.service.uuid]
            )
            print(f"🔗 Connected to {connection.device}")
            self.connected_device = connection

            # Handle BLE communication
            await self.handle_ble(connection)

    async def handle_ble(self, connection):
        """Handle BLE Write requests and respond with Notify"""
        try:
            while connection.is_connected():
                try:
                    conn2, data = await asyncio.wait_for(self.notify_char.written(), 1)
                    if data:
                        print(data)
                        await self.send_data()
                except asyncio.TimeoutError:
                    continue
        except Exception as e:
            print(f"❌ Connection Error: {e}")

    async def send_data(self):
        """Send a single batch of dummy data via Notify"""
        dummy_data = [
            {"id": i, "value": f"Data {i}"} for i in range(_BLE_CHUNK_SIZE * _TOTAL_BATCHES)
        ]

        for i in range(0, len(dummy_data), _BLE_CHUNK_SIZE):
            batch = dummy_data[i:i + _BLE_CHUNK_SIZE]
            json_payload = json.dumps({"data": batch}).encode('utf-8') 

            try:
                # Write data to characteristic (for subscribers)
                print("📤 Writing data to characteristic...")
                self.notify_char.write(json_payload, send_update=True) 

            except Exception as e:
                print(f"❌ BLE Notify Error: {e}")

# Main Execution
ble_server = TestBLEServer()
asyncio.run(ble_server.advertise())
