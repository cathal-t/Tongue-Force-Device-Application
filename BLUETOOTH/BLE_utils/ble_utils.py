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

# Data and threading variables
data_lock = threading.Lock()
time_data = []
sensor_data = []
max_sensor_value = None
stop_event = threading.Event()
read_thread = None
client = None  # BLE client object

# Logging for debug
logging.basicConfig(level=logging.DEBUG)

# Function to handle BLE data received via notifications
def handle_notification(sender, data):
    global max_sensor_value
    timestamp = time()

    # Example: Assuming the data comes as a 32-bit float in binary format (4 bytes)
    try:
        if len(data) == 4:  # Check if data length matches expected size for a 32-bit float
            force_value = struct.unpack('f', data)[0]  # Unpack the binary data as a float
            logging.debug(f"Decoded force value: {force_value}")
        else:
            logging.error(f"Unexpected data length: {len(data)}")
            return

    except Exception as e:
        logging.error(f"Error decoding BLE data: {e}")
        return

    # Store the data in the shared data structures
    with data_lock:
        time_data.append(timestamp)
        sensor_data.append(force_value)

        # Update max sensor value if necessary
        if max_sensor_value is None or force_value > max_sensor_value:
            max_sensor_value = force_value

    logging.debug(f"Received sensor data: {force_value} at {timestamp}")

# Function to start reading data from BLE
async def read_ble_data():
    global client

    try:
        async with BleakClient(DEVICE_ADDRESS) as client:
            logging.info(f"Connected to BLE device at {DEVICE_ADDRESS}")
            await client.start_notify(SENSOR_CHARACTERISTIC_UUID, handle_notification)

            # Keep running until stop event is triggered
            while not stop_event.is_set():
                await asyncio.sleep(0.1)  # Allow the event loop to run

            await client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
            logging.info("Stopped notification from BLE device.")

    except Exception as e:
        logging.error(f"Failed to connect or read from BLE device: {e}")

# Wrapper to start BLE reading in a thread (similar to current threading model)
def start_ble_thread():
    global read_thread
    stop_event.clear()

    if read_thread is None or not read_thread.is_alive():
        read_thread = threading.Thread(target=lambda: asyncio.run(read_ble_data()))
        read_thread.start()
        logging.info("BLE read thread started.")

# Function to stop the BLE thread and disconnect
def stop_ble_thread():
    stop_event.set()

    if read_thread and read_thread.is_alive():
        read_thread.join()
        logging.info("BLE read thread stopped.")

    # Reset data
    with data_lock:
        time_data.clear()
        sensor_data.clear()
        max_sensor_value = None

# This function can be extended to handle reconnection attempts
def reconnect_if_needed():
    if not client or not client.is_connected:
        logging.info("Attempting to reconnect...")
        start_ble_thread()

# BLE-specific open connection function
def open_ble_connection():
    start_ble_thread()

# BLE-specific close connection function
def close_ble_connection():
    stop_ble_thread()

