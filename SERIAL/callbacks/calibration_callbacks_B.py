from dash import Input, Output, State, html, callback_context
import numpy as np
from datetime import datetime
import os
import sys
import threading
from dash.exceptions import PreventUpdate

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import ble_utils  # Import only ble_utils

def register_callbacks(app):

    # Callback to start/stop recording
    @app.callback(
        [
            Output('start-button', 'disabled'),
            Output('stop-button', 'disabled')
        ],
        [
            Input('start-button', 'n_clicks'),
            Input('stop-button', 'n_clicks')
        ]
    )
    def start_stop_recording(start_clicks, stop_clicks):
        start_clicks = start_clicks or 0
        stop_clicks = stop_clicks or 0

        if start_clicks > stop_clicks:
            # Start recording
            ble_utils.start_ble_communication()
            return True, False  # Disable the start button, enable the stop button
        elif stop_clicks > start_clicks:
            # Stop recording
            ble_utils.stop_ble_communication()
            return False, True  # Enable the start button, disable the stop button
        else:
            # Initial state
            return False, True  # Enable start button, disable stop button

    # Callback to update live sensor value
    @app.callback(
        Output('live-sensor-value-calibration', 'children'),
        [Input('live-update-interval', 'n_intervals')],
        [State('start-button', 'disabled')]
    )
    def update_live_sensor_value(n_intervals, start_button_disabled):
        is_recording = start_button_disabled  # True when recording is active

        if is_recording:
            with ble_utils.data_lock:
                if ble_utils.sensor_data:
                    current_sensor_value = ble_utils.sensor_data[-1]
                else:
                    current_sensor_value = "N/A"
            return f"{current_sensor_value}"
        else:
            return "N/A"

    # Callback to update calibration data store
    @app.callback(
        Output('calibration-data-store', 'data'),
        [Input('add-calibration-data-btn', 'n_clicks'),
         Input('reset-calibration-btn', 'n_clicks')],
        [State('applied-weight-input', 'value'),
         State('sensor-value-input', 'value'),
         State('start-button', 'disabled'),
         State('calibration-data-store', 'data')]
    )
    def update_calibration_data(add_clicks, reset_clicks, applied_weight, sensor_value_input, start_button_disabled, data):
        is_recording = start_button_disabled  # True when recording is active
        ctx = callback_context
        if not ctx.triggered:
            return data
        else:
            button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
        if data is None:
            data = []
    
        if button_id == 'add-calibration-data-btn':
            if add_clicks and add_clicks > 0 and applied_weight is not None:
                if sensor_value_input is None and is_recording:
                    # Use live sensor value
                    with ble_utils.data_lock:
                        if ble_utils.sensor_data:
                            sensor_value = ble_utils.sensor_data[-1]
                        else:
                            sensor_value = None
                    if sensor_value is None:
                        # Provide user feedback (you can adjust this as needed)
                        print("Sensor value not available. Please ensure the device is connected and transmitting data.")
                        return data
                else:
                    sensor_value = sensor_value_input
    
                if sensor_value is not None:
                    # Avoid in-place mutation
                    new_data = data.copy()
                    new_data.append({'applied_weight': applied_weight, 'sensor_value': sensor_value})
                    return new_data
                else:
                    return data
            else:
                return data
    
        elif button_id == 'reset-calibration-btn':
            # Clear the calibration data
            return []
        else:
            return data

    # Callback to update calibration data table
    @app.callback(
        Output('calibration-data-table', 'children'),
        [Input('calibration-data-store', 'data')]
    )
    def update_calibration_table(data):
        if not data:
            return html.Div("No calibration data added yet.")
        else:
            table_header = [
                html.Tr([html.Th("Applied Weight (Newtons)"), html.Th("Sensor Value")])
            ]
            table_rows = [
                html.Tr([html.Td(item['applied_weight']), html.Td(item['sensor_value'])]) for item in data
            ]
            return html.Table(children=table_header + table_rows, style={'margin': '0 auto'})

    # Callback to calculate the line of best fit and update coefficients store
    @app.callback(
        [
            Output('calibration-result', 'children'),
            Output('calibration-coefficients-store', 'data')
        ],
        [
            Input('calculate-fit-btn', 'n_clicks'),
            Input('reset-calibration-btn', 'n_clicks')
        ],
        [State('calibration-data-store', 'data')]
    )
    def update_calibration_result(calculate_clicks, reset_clicks, data):
        ctx = callback_context
        if not ctx.triggered:
            return "", {}
        else:
            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger_id == 'calculate-fit-btn':
            if calculate_clicks and calculate_clicks > 0:
                if data and len(data) >= 2:
                    applied_weights = np.array([item['applied_weight'] for item in data])
                    sensor_values = np.array([item['sensor_value'] for item in data])

                    # Perform linear regression (best fit line)
                    slope, intercept = np.polyfit(sensor_values, applied_weights, 1)

                    # Create a dictionary to store the coefficients
                    coefficients = {'slope': slope, 'intercept': intercept}

                    result_text = f"Line of Best Fit: Force = {slope:.4f} * Sensor Value + {intercept:.4f}"
                    return result_text, coefficients
                else:
                    return "Please enter at least two calibration data points.", {}
            else:
                return "", {}
        elif trigger_id == 'reset-calibration-btn':
            return "", {}  # Clear the calibration result and coefficients when reset is clicked
        else:
            return "", {}

    # Callback to save calibration data
    @app.callback(
        [
            Output('calibration-save-confirmation', 'children'),
            Output('shared-calibration-coefficients', 'data')
        ],
        [Input('save-calibration-btn', 'n_clicks')],
        [State('calibration-coefficients-store', 'data')]
    )
    def save_calibration_data(n_clicks, coefficients):
        if n_clicks and n_clicks > 0:
            if not coefficients:
                return "No calibration coefficients to save. Please calculate the line of best fit first.", {}

            # Extract slope and intercept
            calibration_slope = coefficients.get('slope')
            calibration_intercept = coefficients.get('intercept')

            # Save calibration data
            filename = os.path.join(os.path.dirname(__file__), '..', 'calibration_data.txt')
            try:
                with open(filename, 'w') as f:
                    f.write(f'{calibration_slope},{calibration_intercept}')
                # Update the shared calibration coefficients store
                shared_coefficients = {'slope': calibration_slope, 'intercept': calibration_intercept}
                return f"Calibration data saved.", shared_coefficients
            except Exception as e:
                return f"Error saving calibration data: {e}", {}
        else:
            return "", {}
