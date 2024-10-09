from dash import Input, Output, State, html, callback_context
import numpy as np
from datetime import datetime
import os
from utils.communication_utils import comm_handler  # Use the generic communication handler

def register_callbacks(app):
    # Callback to monitor and update connection status
    @app.callback(
        Output('connection-status_calibration', 'children'),
        [Input('live-update-interval', 'n_intervals')]
    )
    def update_connection_status(n_intervals):
        if comm_handler.mode == 'BLE':
            if comm_handler.is_connected():
                return html.Div("Connected to BLE device.", style={'color': '#28a745', 'font-weight': 'bold'})
            elif comm_handler.is_connecting():
                return html.Div("Attempting to connect to BLE device...", style={'color': '#ffc107', 'font-weight': 'bold'})
            else:
                return html.Div("Disconnected from BLE device.", style={'color': '#dc3545', 'font-weight': 'bold'})
        else:
            # Optionally, display nothing or a message for other modes
            return html.Div("")

    # Callback to start/stop recording
    @app.callback(
        [
            Output('calibration-start-button', 'disabled'),
            Output('calibration-stop-button', 'disabled')
        ],
        [
            Input('calibration-start-button', 'n_clicks'),
            Input('calibration-stop-button', 'n_clicks')
        ]
    )
    def start_stop_recording(start_clicks, stop_clicks):
        print(f"Start clicks: {start_clicks}, Stop clicks: {stop_clicks}")  # Debugging statement

        start_clicks = start_clicks or 0
        stop_clicks = stop_clicks or 0

        # Check which button triggered the callback
        ctx = callback_context
        if not ctx.triggered:
            return False, True  # Initial state: start enabled, stop disabled
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'calibration-start-button':
            # Start recording
            print("Start recording clicked.")
            comm_handler.clear_data()
            comm_handler.start_reading()
            print("Data reading started.")

            return True, False  # Disable the start button, enable the stop button

        elif button_id == 'calibration-stop-button':
            # Stop recording
            print("Stop recording clicked.")
            comm_handler.stop_reading()
            comm_handler.clear_data()  # If you wish to clear data after stopping

            return False, True  # Enable the start button, disable the stop button

        return False, True  # Fallback in case no button was clicked

    # Callback to update live sensor value
    @app.callback(
        Output('live-sensor-value-calibration', 'children'),
        [Input('live-update-interval', 'n_intervals')],
        [State('calibration-start-button', 'disabled')]
    )
    def update_live_sensor_value(n_intervals, start_button_disabled):
        is_recording = start_button_disabled  # True when recording is active
        if is_recording:
            sensor_data = comm_handler.get_sensor_data()
            if sensor_data:
                current_sensor_value = round(sensor_data[-1], 1)
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
         State('calibration-start-button', 'disabled'),
         State('calibration-data-store', 'data')]
    )
    def update_calibration_data(add_clicks, reset_clicks, applied_weight, sensor_value, start_button_disabled, data):
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
                if sensor_value is None and is_recording:
                    # Use live sensor value
                    sensor_data = comm_handler.get_sensor_data()
                    if sensor_data:
                        sensor_value = sensor_data[-1]
                    else:
                        sensor_value = None

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
