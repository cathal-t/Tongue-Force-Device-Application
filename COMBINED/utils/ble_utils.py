import asyncio
import threading
from bleak import BleakClient
from time import time
import logging
import struct

# Device-specific information
DEVICE_ADDRESS = "96:18:FC:FA:30:FA"
SENSOR_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Logging for debug
logging.basicConfig(level=logging.DEBUG)

# BLECommunicator class
class BLECommunicator:
    def __init__(self):
        self.client = None  # BLE client object
        self._is_connected = False
        self._is_connecting = False
        self._is_notifying = False
        self.loop = asyncio.new_event_loop()
        self.connection_lock = threading.Lock()
        self.data_lock = threading.Lock()
        self.time_data = []
        self.sensor_data = []
        self.max_sensor_value = None
        self.connection_event = threading.Event()  # Event to signal when connected

        # Start the event loop in a separate thread
        threading.Thread(target=self._run_event_loop, daemon=True).start()

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    # Function to handle BLE data received via notifications
    def handle_notification(self, sender, data):
        timestamp = time()

        try:
            if len(data) == 4:  # Assuming the data is a 32-bit float
                force_value = struct.unpack('f', data)[0]
                logging.debug(f"Decoded force value: {force_value}")
            else:
                logging.error(f"Unexpected data length: {len(data)}")
                return

        except Exception as e:
            logging.error(f"Error decoding BLE data: {e}")
            return

        # Store the data in the shared data structures
        with self.data_lock:
            self.time_data.append(timestamp)
            self.sensor_data.append(force_value)

            # Update max sensor value
            if self.max_sensor_value is None or force_value > self.max_sensor_value:
                self.max_sensor_value = force_value

        logging.debug(f"Received sensor data: {force_value} at {timestamp}")

    # Async function to connect to BLE device
    async def connect(self):
        with self.connection_lock:
            if self._is_connected or self._is_connecting:
                return

            self._is_connecting = True
            try:
                self.client = BleakClient(DEVICE_ADDRESS, loop=self.loop)
                await self.client.connect()
                self._is_connected = True
                self.connection_event.set()  # Signal that connection is established
                logging.info(f"Connected to BLE device at {DEVICE_ADDRESS}")

            except Exception as e:
                logging.error(f"Failed to connect to BLE device: {e}")
                self._is_connected = False
                self.connection_event.clear()

            finally:
                self._is_connecting = False

    # Function to start BLE connection
    def start_connection(self):
        if self._is_connected or self._is_connecting:
            return

        self.connection_event.clear()  # Reset the event
        asyncio.run_coroutine_threadsafe(self.connect(), self.loop)
        logging.info("BLE connection initiated.")

    # Async function to start notifications
    async def start_notifications(self):
        with self.connection_lock:
            if not self._is_connected or self._is_connecting or self._is_notifying:
                return

            try:
                await self.client.start_notify(SENSOR_CHARACTERISTIC_UUID, self.handle_notification)
                self._is_notifying = True
                logging.info("Started notifications from BLE device.")

            except Exception as e:
                logging.error(f"Failed to start notifications: {e}")

    # Function to start reading data
    def start_reading(self):
        if not self._is_connected:
            # Start the connection if not connected
            self.start_connection()

        # Wait for the connection to be established
        if not self.connection_event.wait(timeout=10):
            logging.error("Failed to establish BLE connection within timeout.")
            return

        # Start notifications
        asyncio.run_coroutine_threadsafe(self.start_notifications(), self.loop)

    # Async function to stop notifications
    async def stop_notifications(self):
        with self.connection_lock:
            if not self._is_notifying:
                return

            try:
                await self.client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
                self._is_notifying = False
                logging.info("Stopped notifications from BLE device.")

            except Exception as e:
                logging.error(f"Failed to stop notifications: {e}")

    # Function to stop reading data
    def stop_reading(self):
        asyncio.run_coroutine_threadsafe(self.stop_notifications(), self.loop)

    # Async function to disconnect from BLE device
    async def disconnect(self):
        with self.connection_lock:
            if not self._is_connected:
                return

            try:
                if self._is_notifying:
                    await self.client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
                    self._is_notifying = False
                    logging.info("Stopped notifications from BLE device during disconnect.")

                await self.client.disconnect()
                logging.info("BLE client disconnected.")
            except Exception as e:
                logging.error(f"Failed to disconnect BLE client: {e}")

            self._is_connected = False
            self.client = None
            self.connection_event.clear()

    # Function to disconnect from BLE device
    def close_connection(self):
        future = asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)
        try:
            # Wait for the disconnect to complete
            future.result(timeout=5)
        except Exception as e:
            logging.error(f"Error during BLE disconnect: {e}")

    # Function to get the sensor data
    def get_sensor_data(self):
        with self.data_lock:
            return self.sensor_data.copy()

    def get_time_data(self):
        with self.data_lock:
            return self.time_data.copy()

    def get_max_sensor_value(self):
        with self.data_lock:
            return self.max_sensor_value

    def clear_data(self):
        with self.data_lock:
            self.time_data.clear()
            self.sensor_data.clear()
            self.max_sensor_value = None

    # Function to check connection status
    def is_connected(self):
        return self._is_connected

    def is_connecting(self):
        return self._is_connecting

    def is_notifying(self):
        return self._is_notifying
