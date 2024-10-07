import asyncio
import threading
import time
import struct
from bleak import BleakClient
import nest_asyncio

nest_asyncio.apply()  # Allows nested event loops

# Replace with your Arduino's MAC address
DEVICE_ADDRESS = "96:18:FC:FA:30:FA"

# UUIDs from your Arduino code
SENSOR_SERVICE_UUID = "12345678-1234-5678-1234-56789abcdef0"
SENSOR_CHARACTERISTIC_UUID = "12345678-1234-5678-1234-56789abcdef1"

# Shared variables for sensor data
sensor_value = None
max_sensor_value = None
sensor_data = []
time_data = []
data_lock = threading.Lock()

# Event to signal the BLE client loop to stop
stop_event = threading.Event()

# Variables to hold the BLE client and event loop
ble_client = None
ble_loop_thread = None
ble_loop = None

def notification_handler(sender, data):
    global sensor_value, max_sensor_value
    with data_lock:
        try:
            # Unpack the bytes to a float (little-endian format)
            sensor_value = struct.unpack('<f', data)[0]
            current_time = time.time()
            sensor_data.append(sensor_value)
            time_data.append(current_time)
            if max_sensor_value is None or sensor_value > max_sensor_value:
                max_sensor_value = sensor_value
        except struct.error as e:
            print(f"Error unpacking data: {e}")

async def run_ble_client():
    global ble_client
    while not stop_event.is_set():
        try:
            ble_client = BleakClient(DEVICE_ADDRESS)
            await ble_client.connect()
            if not ble_client.is_connected:
                print("Failed to connect to the BLE device.")
                await asyncio.sleep(5)
                continue

            print("Connected to the BLE device.")

            await ble_client.start_notify(SENSOR_CHARACTERISTIC_UUID, notification_handler)

            while ble_client.is_connected and not stop_event.is_set():
                await asyncio.sleep(1)

            await ble_client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
            await ble_client.disconnect()
            print("Disconnected from the BLE device.")
        except Exception as e:
            print(f"BLE connection error: {e}")
            await asyncio.sleep(5)

    # Clean up the client
    if ble_client and ble_client.is_connected:
        await ble_client.disconnect()

async def stop_ble_client():
    global ble_client
    if ble_client and ble_client.is_connected:
        await ble_client.stop_notify(SENSOR_CHARACTERISTIC_UUID)
        await ble_client.disconnect()
        print("BLE client disconnected.")

def start_ble_communication():
    global ble_loop_thread, stop_event, ble_loop
    if ble_loop_thread and ble_loop_thread.is_alive():
        print("BLE communication is already running.")
        return
    stop_event.clear()
    ble_loop_thread = threading.Thread(target=start_ble_loop)
    ble_loop_thread.daemon = True  # Ensure thread exits when main program exits
    ble_loop_thread.start()
    print("BLE communication started.")

def stop_ble_communication():
    global ble_client, stop_event, ble_loop_thread, ble_loop
    if not ble_loop_thread:
        print("BLE communication is not running.")
        return
    stop_event.set()

    # Schedule the stop_ble_client coroutine to run in the event loop
    if ble_loop and ble_loop.is_running():
        asyncio.run_coroutine_threadsafe(stop_ble_client(), ble_loop)

    # Wait for the BLE loop thread to finish
    if ble_loop_thread and ble_loop_thread.is_alive():
        ble_loop_thread.join()
        print("BLE communication stopped.")

    # Reset variables
    ble_loop = None
    ble_loop_thread = None

    # Reset data
    with data_lock:
        global sensor_value, max_sensor_value
        sensor_value = None
        max_sensor_value = None
        sensor_data.clear()
        time_data.clear()

def start_ble_loop():
    global ble_loop
    # Create a new event loop for this thread
    ble_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(ble_loop)
    ble_loop.run_until_complete(run_ble_client())
    # Clean up the event loop
    ble_loop.close()
    print("BLE loop closed.")
