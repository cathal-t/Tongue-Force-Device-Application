import serial
import threading
import time

# Global variables for the serial data
ser = None
stop_event = threading.Event()  # Event to signal the thread to stop
time_data = []
sensor_data = []
max_sensor_value = None  # Initialize as None
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
        ser = None  # Ensure ser is None if opening fails

def close_serial_port():
    global ser
    print("Attempting to close serial port.")
    if ser and ser.is_open:
        try:
            ser.flushInput()  # Flush the input buffer
            ser.close()  # Close the serial port
            print("Serial port closed successfully.")
        except Exception as e:
            print(f"Error closing serial port: {e}")
    else:
        print("Serial port already closed or not open.")  # Handle already closed port
    ser = None  # Reset the serial object

# Thread function to read serial data and update global variables
def read_serial_data():
    global time_data, sensor_data, max_sensor_value
    start_time = time.time()  # Start time for the data recording session

    while not stop_event.is_set():
        try:
            if ser and ser.is_open and ser.in_waiting:  # Check if data is available on the serial port
                line = ser.readline().decode('utf-8', errors='replace').strip()  # Read and decode the serial input

                try:
                    sensor_value = float(line)
                    elapsed_time = time.time() - start_time

                    # Lock the data while updating to prevent race conditions
                    with data_lock:
                        time_data.append(elapsed_time)
                        sensor_data.append(sensor_value)

                        # Update max_sensor_value only if sensor_value is higher
                        if max_sensor_value is None or sensor_value > max_sensor_value:
                            max_sensor_value = sensor_value
                            print(f"New max sensor value: {max_sensor_value}")  # Debugging statement

                except ValueError:
                    print(f"Warning: Invalid data received: {line}")  # Print warning for invalid data

        except Exception as e:
            print(f"Error reading data: {e}")

        time.sleep(0.01)  # Adjusted delay to prevent excessive CPU usage
