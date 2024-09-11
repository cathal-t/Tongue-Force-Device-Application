import serial
import threading
import time

# Global variables for the serial data
ser = None
stop_event = threading.Event()  # Event to signal the thread to stop
time_data = []
sensor_data = []
max_sensor_value = 0
read_thread = None
data_lock = threading.Lock()  # Lock to ensure thread safety

# Function to open the serial port
def open_serial_port():
    global ser
    try:
        if ser is None or not ser.is_open:
            ser = serial.Serial('COM3', 9600, timeout=1)
            ser.flushInput()  # Flush the input buffer to remove any stale data
            print(f"Serial port {ser.port} opened successfully.")
    except serial.SerialException as e:
        print(f"Error: {e}")

# Function to close the serial port safely
def close_serial_port():
    global ser
    if ser and ser.is_open:
        try:
            ser.flushInput()  # Flush the input buffer to ensure no data is left
            ser.close()
            print("Serial port closed.")
        except Exception as e:
            print(f"Error closing serial port: {e}")

# Thread function to read serial data and update global variables
def read_serial_data():
    global time_data, sensor_data, max_sensor_value
    start_time = time.time()  # Start time for the data recording session

    while not stop_event.is_set():
        try:
            if ser and ser.is_open and ser.in_waiting:  # Check if data is available on the serial port
                line = ser.readline().decode('utf-8', errors='replace').strip()  # Read and decode the serial input

                if line.isdigit():  # Ensure the line contains valid integer data
                    sensor_value = int(line)
                    elapsed_time = time.time() - start_time

                    # Lock the data while updating to prevent race conditions
                    with data_lock:
                        time_data.append(elapsed_time)
                        sensor_data.append(sensor_value)

                        # Update max_sensor_value only if sensor_value is higher
                        if sensor_value > max_sensor_value:
                            max_sensor_value = sensor_value
                            print(f"New max sensor value: {max_sensor_value}")  # Debugging statement

                else:
                    print(f"Warning: Invalid data received: {line}")  # Print warning for invalid data

        except Exception as e:
            print(f"Error reading data: {e}")

        time.sleep(0.0001)  # Small delay to prevent excessive CPU usage
