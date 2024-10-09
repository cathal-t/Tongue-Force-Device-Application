# utils/communication_utils.py

from utils.serial_utils import SerialCommunicator
from utils.ble_utils import BLECommunicator
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Define CommunicationHandler class
class CommunicationHandler:
    def __init__(self, mode='BLE'):  # Default mode is now set to BLE
        self.mode = None  # Initially, set mode to None
        self.handler = None
        self.set_mode(mode)  # Set the initial mode (Serial or BLE)

    def set_mode(self, mode):
        # If mode is changing, ensure the current connection is closed
        if self.handler:
            self.close_connection()

        self.mode = mode
        logging.info(f"Setting communication mode to {mode}")

        # Set the appropriate communication handler (Serial or BLE)
        if mode == 'Serial':
            self.handler = SerialCommunicator()
        elif mode == 'BLE':
            self.handler = BLECommunicator()
        else:
            raise ValueError(f"Unknown communication mode: {mode}")

    def start_reading(self):
        if not self.handler:
            logging.error("No communication handler initialized.")
            return
        logging.info(f"Starting data reading using {self.mode} mode.")
        self.handler.start_reading()

    def stop_reading(self):
        if not self.handler:
            logging.error("No communication handler initialized.")
            return
        logging.info(f"Stopping data reading using {self.mode} mode.")
        self.handler.stop_reading()

    def close_connection(self):
        if not self.handler:
            logging.error("No communication handler initialized.")
            return
        logging.info(f"Closing connection using {self.mode} mode.")
        self.handler.close_connection()

    def clear_data(self):
        if self.handler:
            self.handler.clear_data()

    def is_connected(self):
        if self.handler:
            return self.handler.is_connected()
        else:
            return False

    def is_connecting(self):
        if self.handler:
            return self.handler.is_connecting()
        else:
            return False

    def get_time_data(self):
        if self.handler:
            return self.handler.get_time_data()
        else:
            return []

    def get_sensor_data(self):
        if self.handler:
            return self.handler.get_sensor_data()
        else:
            return []

    def get_max_sensor_value(self):
        if self.handler:
            return self.handler.get_max_sensor_value()
        else:
            return None

# Define a global comm_handler instance
comm_handler = CommunicationHandler(mode='BLE')  # Default mode is now BLE
