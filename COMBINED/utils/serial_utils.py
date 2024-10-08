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

class SerialCommunicator:
    def __init__(self):
        self.ser = None
        self.stop_event = threading.Event()  # Local event for this instance
        self.read_thread = None
        self._is_connected = False
        self._is_connecting = False

    # Function to open the serial port
    def open_serial_port(self):
        try:
            if self.ser is None or not self.ser.is_open:
                self.ser = serial.Serial('COM6', 9600, timeout=1)
                self.ser.flushInput()  # Flush the input buffer to remove any stale data
                print(f"Serial port {self.ser.port} opened successfully.")
                self._is_connected = True
                self._is_connecting = False
        except serial.SerialException as e:
            print(f"Error: {e}")
            self.ser = None  # Ensure ser is None if opening fails
            self._is_connected = False
            self._is_connecting = False

    # Function to close the serial port
    def close_serial_port(self):
        print("Attempting to close serial port.")
        if self.ser and self.ser.is_open:
            try:
                self.ser.flushInput()  # Flush the input buffer
                self.ser.close()  # Close the serial port
                print("Serial port closed successfully.")
            except Exception as e:
                print(f"Error closing serial port: {e}")
        else:
            print("Serial port already closed or not open.")  # Handle already closed port
        self.ser = None  # Reset the serial object
        self._is_connected = False
        self._is_connecting = False

    # Thread function to read serial data and update global variables
    def read_serial_data(self):
        global time_data, sensor_data, max_sensor_value
        start_time = time.time()  # Start time for the data recording session

        while not self.stop_event.is_set():
            try:
                if self.ser and self.ser.is_open and self.ser.in_waiting:  # Check if data is available on the serial port
                    line = self.ser.readline().decode('utf-8', errors='replace').strip()  # Read and decode the serial input

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

    # Method to start reading data
    def start_reading(self):
        self.open_serial_port()
        if not self.read_thread or not self.read_thread.is_alive():
            self.stop_event.clear()
            self.read_thread = threading.Thread(target=self.read_serial_data)
            self.read_thread.start()
            self._is_connecting = True

    # Method to stop reading data
    def stop_reading(self):
        self.stop_event.set()
        if self.read_thread and self.read_thread.is_alive():
            self.read_thread.join()
        self.close_serial_port()

    # Method to get the sensor data
    def get_sensor_data(self):
        global sensor_data
        with data_lock:
            return sensor_data.copy()

    def get_time_data(self):
        global time_data
        with data_lock:
            return time_data.copy()

    def get_max_sensor_value(self):
        global max_sensor_value
        with data_lock:
            return max_sensor_value

    def clear_data(self):
        global time_data, sensor_data, max_sensor_value
        with data_lock:
            time_data.clear()
            sensor_data.clear()
            max_sensor_value = None

    # Function to check connection status
    def is_connected(self):
        return self._is_connected

    def is_connecting(self):
        return self._is_connecting

    # Method to close the connection
    def close_connection(self):
        self.stop_reading()
