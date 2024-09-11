from dash import Input, Output, State
import numpy as np
from dash import html
from datetime import datetime
import os
import sys
import threading
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.serial_utils import open_serial_port, close_serial_port, read_serial_data, stop_event, time_data, sensor_data, max_sensor_value, read_thread, data_lock

# Store calibration data in memory
calibration_data = []
calibration_slope, calibration_intercept = 1, 0  # Default values

def register_callbacks(app):

    # Unified callback to start/stop recording sensor data and disable/enable graph update
    @app.callback(
        [Output('graph-update-calibration', 'disabled'),
         Output('live-sensor-value-calibration', 'children')],
        [Input('start-button', 'n_clicks'),
         Input('graph-update-calibration', 'n_intervals')],
        [State('start-button', 'n_clicks')]
    )
    def start_recording_and_update_live_value(start_clicks, n_intervals, start_clicks_state):
        if start_clicks_state > 0:
            stop_event.clear()  # Clear stop event to allow recording
            time_data.clear()
            sensor_data.clear()
            open_serial_port()

            # Start data reading thread if not already running
            global read_thread
            if read_thread is None or not read_thread.is_alive():
                read_thread = threading.Thread(target=read_serial_data)
                read_thread.start()

            # Acquire live sensor value during recording
            with data_lock:
                current_sensor_value = sensor_data[-1] if sensor_data else "N/A"
            return False, f"{current_sensor_value} N"  # Enable graph update and return live value

        else:
            stop_event.set()  # Stop the recording
            if read_thread and read_thread.is_alive():
                read_thread.join()
            close_serial_port()
            return True, "N/A"  # Disable graph update and reset sensor value

    # Callback to add calibration data
    @app.callback(
        Output('calibration-data-table', 'children'),
        [Input('add-calibration-data-btn', 'n_clicks')],
        [State('applied-weight-input', 'value'),
         State('sensor-value-input', 'value'),
         State('start-button', 'n_clicks')]  # To check if recording is active
    )
    def add_calibration_data(n_clicks, applied_weight, sensor_value, start_clicks):
        if n_clicks > 0 and applied_weight is not None:
            # If sensor value is not provided, use live sensor value
            if start_clicks > 0 and not sensor_value:
                with data_lock:
                    sensor_value = sensor_data[-1] if sensor_data else None

            if sensor_value is not None:
                calibration_data.append((applied_weight, sensor_value))
                return generate_table(calibration_data)
        return generate_table([])  # Return an empty table if no data

    # Helper function to generate the table from calibration data
    def generate_table(data):
        table_header = [
            html.Tr([html.Th("Applied Weight (Newtons)"), html.Th("Sensor Value")])
        ]
        table_rows = [
            html.Tr([html.Td(weight), html.Td(sensor)]) for weight, sensor in data
        ]
        return html.Table(children=table_header + table_rows)

    # Callback to calculate the line of best fit
    @app.callback(
        Output('calibration-result', 'children'),
        [Input('calculate-fit-btn', 'n_clicks')]
    )
    def calculate_line_of_best_fit(n_clicks):
        if n_clicks > 0 and len(calibration_data) >= 2:
            applied_weights = np.array([point[0] for point in calibration_data])
            sensor_values = np.array([point[1] for point in calibration_data])

            # Perform linear regression (best fit line)
            slope, intercept = np.polyfit(sensor_values, applied_weights, 1)
            
            # Store calibration coefficients globally
            global calibration_slope, calibration_intercept
            calibration_slope = slope
            calibration_intercept = intercept

            return f"Line of Best Fit: Force = {slope:.4f} * Sensor Value + {intercept:.4f}"
        return "Please enter more data for calibration."

    # Callback to save calibration data
    @app.callback(
        Output('calibration-save-confirmation', 'children'),
        [Input('save-calibration-btn', 'n_clicks')]
    )
    def save_calibration_data(n_clicks):
        if n_clicks > 0:
            # Save calibration data with timestamp
            filename = f'calibration_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
            with open(filename, 'w') as f:
                f.write(f'{calibration_slope},{calibration_intercept}')
            return f"Calibration data saved to {filename}."
        return ""
