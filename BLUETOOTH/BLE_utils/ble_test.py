import time
import logging
import ble_utils  # Import the new BLE utility module


# Set up logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

def test_ble_connection():
    try:
        # Step 1: Open BLE connection
        logging.info("Opening BLE connection...")
        ble_utils.open_ble_connection()

        # Step 2: Allow some time for data to be collected
        logging.info("Collecting data for 10 seconds...")
        time.sleep(10)  # Adjust the duration as needed

        # Step 3: Print collected data (time_data and sensor_data)
        with ble_utils.data_lock:
            if ble_utils.sensor_data:
                logging.info("Collected sensor data:")
                for t, d in zip(ble_utils.time_data, ble_utils.sensor_data):
                    logging.info(f"Time: {t}, Force: {d}")
            else:
                logging.warning("No data received from BLE device.")

        # Step 4: Stop BLE connection
        logging.info("Stopping BLE connection...")
        ble_utils.close_ble_connection()

    except Exception as e:
        logging.error(f"An error occurred during BLE testing: {e}")

if __name__ == "__main__":
    test_ble_connection()
