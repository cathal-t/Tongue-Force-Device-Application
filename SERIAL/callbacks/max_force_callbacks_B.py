from dash import Input, Output, State
from datetime import datetime
import pandas as pd
import threading
import plotly.graph_objs as go
import os
import sys
import numpy as np
import re
from dash.exceptions import PreventUpdate

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import ble_utils  # Import only ble_utils

# Initialize current timestamp
current_timestamp = None

def register_callbacks(app):
    # Callback for updating the live graph and sensor values
    @app.callback(
        Output('live-graph', 'figure'),
        [Input('graph-update', 'n_intervals')],
        [State('shared-calibration-coefficients', 'data')]
    )
    def update_graph(n, calibration_coefficients):
        with ble_utils.data_lock:
            if len(ble_utils.time_data) == 0 or len(ble_utils.sensor_data) == 0:
                return go.Figure()

            current_time = ble_utils.time_data[-1]
            window_start = max(0, current_time - 10)

            # Extract calibration coefficients
            if calibration_coefficients:
                calibration_slope = calibration_coefficients.get('slope', 1)
                calibration_intercept = calibration_coefficients.get('intercept', 0)
            else:
                calibration_slope = 1
                calibration_intercept = 0

            # Apply calibration to the sensor values
            calibrated_sensor_data = [calibration_slope * s + calibration_intercept for s in ble_utils.sensor_data]

            if not calibrated_sensor_data:
                return go.Figure()

            # Prepare data for the live graph with calibrated values
            data = go.Scatter(
                x=[t for t in ble_utils.time_data if window_start <= t <= current_time],
                y=[s for t, s in zip(ble_utils.time_data, calibrated_sensor_data) if window_start <= t <= current_time],
                mode='lines+markers',
                line=dict(color='#007BFF')
            )

        # Define the layout for the graph
        layout = go.Layout(
            xaxis=dict(range=[window_start, window_start + 10], gridcolor='#ddd'),
            yaxis=dict(
                range=[min(calibrated_sensor_data) - 5, max(calibrated_sensor_data) + 5],
                gridcolor='#ddd'
            ),
            title='Live Sensor Data (Calibrated to Newtons)',
            plot_bgcolor='#fff',
            paper_bgcolor='#f4f4f4',
            font=dict(color='#333'),
            margin=dict(l=40, r=40, t=50, b=40),
        )

        return {'data': [data], 'layout': layout}

    # Callback for live sensor value, max value, and percentages
    @app.callback(
        [
            Output('live-sensor-value', 'children'),
            Output('max-sensor-value', 'children'),
            Output('forty-percent', 'children'),
            Output('sixty-percent', 'children'),
            Output('eighty-percent', 'children')
        ],
        [Input('graph-update', 'n_intervals')],
        [State('shared-calibration-coefficients', 'data')]
    )
    def update_live_and_max_value(n, calibration_coefficients):
        with ble_utils.data_lock:
            if not ble_utils.sensor_data:
                return "N/A", "N/A", "N/A", "N/A", "N/A"

            # Extract calibration coefficients
            if calibration_coefficients:
                calibration_slope = calibration_coefficients.get('slope', 1)
                calibration_intercept = calibration_coefficients.get('intercept', 0)
            else:
                calibration_slope = 1
                calibration_intercept = 0

            # Apply calibration to the current sensor value and max value
            current_value = calibration_slope * ble_utils.sensor_data[-1] + calibration_intercept
            current_max_sensor_value = (
                calibration_slope * ble_utils.max_sensor_value + calibration_intercept
                if ble_utils.max_sensor_value is not None else None
            )

            # Calculate percentages
            if current_max_sensor_value is not None:
                forty_percent = current_max_sensor_value * 0.4
                sixty_percent = current_max_sensor_value * 0.6
                eighty_percent = current_max_sensor_value * 0.8
            else:
                forty_percent, sixty_percent, eighty_percent = None, None, None

        # Format the output strings
        def format_value(val):
            if isinstance(val, (float, int, np.float64, np.float32, np.int64, np.int32)):
                return f"{float(val):.2f}"
            else:
                return "N/A"

        current_value_str = format_value(current_value) + " N"
        current_max_value_str = format_value(current_max_sensor_value) + " N"
        forty_percent_str = format_value(forty_percent)
        sixty_percent_str = format_value(sixty_percent)
        eighty_percent_str = format_value(eighty_percent)

        return (
            current_value_str,
            current_max_value_str,
            forty_percent_str,
            sixty_percent_str,
            eighty_percent_str
        )

    # Callback to start/stop recording
    @app.callback(
        [
            Output('graph-update', 'disabled'),
            Output('id-warning', 'children')
        ],
        [
            Input('start-button', 'n_clicks'),
            Input('stop-button', 'n_clicks')
        ],
        [State('patient-id', 'value')]
    )
    def start_stop_recording(start_clicks, stop_clicks, patient_id):
        global current_timestamp
        start_clicks = start_clicks or 0
        stop_clicks = stop_clicks or 0

        if start_clicks > stop_clicks:
            if not patient_id:
                return True, "Please enter Patient ID."

            ble_utils.start_ble_communication()

            # Generate timestamp for the current session
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            return False, ""  # Enable graph update and clear warning

        elif stop_clicks > 0 and stop_clicks >= start_clicks:
            ble_utils.stop_ble_communication()
            return True, ""
        else:
            # Neither button has been clicked yet
            return True, ""

    # Callback to save the data to a CSV file
    @app.callback(
        Output('save-confirmation', 'children'),
        [Input('save-button', 'n_clicks')],
        [
            State('patient-id', 'value'),
            State('shared-calibration-coefficients', 'data')
        ]
    )
    def save_data_to_csv(n_clicks, patient_id, calibration_coefficients):
        global current_timestamp
        if n_clicks and n_clicks > 0 and patient_id:
            with ble_utils.data_lock:
                if not ble_utils.time_data:
                    return "No data to save. Please record data first."
                if not current_timestamp:
                    current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Extract calibration coefficients
                if calibration_coefficients:
                    calibration_slope = calibration_coefficients.get('slope', 1)
                    calibration_intercept = calibration_coefficients.get('intercept', 0)
                else:
                    calibration_slope = 1
                    calibration_intercept = 0

                # Sanitize patient_id to remove invalid characters
                sanitized_patient_id = re.sub(r'[^A-Za-z0-9_\- ]+', '', patient_id)
                if not sanitized_patient_id:
                    return "Invalid Patient ID."

                # Create the patient's folder inside the 'profiles' directory
                patient_folder = os.path.join('profiles', sanitized_patient_id)
                os.makedirs(patient_folder, exist_ok=True)

                # Create a filename with the current timestamp
                filename = f'{sanitized_patient_id}_{current_timestamp}.csv'
                filepath = os.path.join(patient_folder, filename)
                df = pd.DataFrame({
                    'Time (s)': ble_utils.time_data,
                    'Sensor Value (Newtons)': [
                        calibration_slope * s + calibration_intercept for s in ble_utils.sensor_data
                    ]
                })
                try:
                    df.to_csv(filepath, index=False)
                except Exception as e:
                    return f"Error saving data: {e}"

                # Calculate statistics
                max_force = df['Sensor Value (Newtons)'].max()
                force_20 = max_force * 0.2
                force_40 = max_force * 0.4
                force_60 = max_force * 0.6
                force_80 = max_force * 0.8

                # Save statistics to a separate file
                stats_filename = f'statistics_{current_timestamp}.txt'
                stats_filepath = os.path.join(patient_folder, stats_filename)
                try:
                    with open(stats_filepath, 'w') as stats_file:
                        stats_file.write(f'Max Force: {max_force:.2f} N\n')
                        stats_file.write(f'20% of Max Force: {force_20:.2f} N\n')
                        stats_file.write(f'40% of Max Force: {force_40:.2f} N\n')
                        stats_file.write(f'60% of Max Force: {force_60:.2f} N\n')
                        stats_file.write(f'80% of Max Force: {force_80:.2f} N\n')
                except Exception as e:
                    return f"Error saving statistics: {e}"

                return f'Data saved to {filepath} and statistics saved to {stats_filepath}'
        elif n_clicks and n_clicks > 0 and not patient_id:
            return "Please enter Patient ID."
        return ""
