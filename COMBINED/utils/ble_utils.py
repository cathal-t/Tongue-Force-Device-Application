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
        self.read_thread = None
        self.stop_event = threading.Event()
        self.time_data = []
        self.sensor_data = []
        self.max_sensor_value = None
        self.data_lock = threading.Lock()

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

    # Async function to start reading data from BLE
    async def read_ble_data(self):
        self._is_connecting = True
        try:
            async with BleakClient(DEVICE_ADDRESS) as client:
                self.client = client
                logging.info(f"Connected to BLE device at {DEVICE_ADDRESS}")
                self._is_connected = True
                self._is_connecting = False
                await client.start_notify(SENSOR_CHARACTERISTIC_UUID, self.handle_notification)

                # Keep running until stop event is triggered
                while not self.stop_event.is_set():
                    await asyncio.sleep(0.1)

                await client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
                logging.info("Stopped notification from BLE device.")

        except Exception as e:
            logging.error(f"Failed to connect or read from BLE device: {e}")
            self._is_connected = False
            self._is_connecting = False

        finally:
            self._is_connected = False
            self._is_connecting = False

    # Function to start BLE reading in a thread
    def start_reading(self):
        self.stop_event.clear()
        if self.read_thread is None or not self.read_thread.is_alive():
            self.read_thread = threading.Thread(target=lambda: asyncio.run(self.read_ble_data()))
            self.read_thread.start()
            logging.info("BLE read thread started.")
            self._is_connecting = True

    # Function to stop BLE reading
    def stop_reading(self):
        self.stop_event.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join()
            logging.info("BLE read thread stopped.")
        self._is_connected = False
        self._is_connecting = False

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

    # Function to close BLE connection
    def close_connection(self):
        self.stop_reading()
