from dash import Input, Output, State, callback_context
from datetime import datetime
import pandas as pd
import threading
import plotly.graph_objs as go
import os
import sys
import numpy as np
import re
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from BLE_utils import ble_utils  # Updated import to use BLE

# Remove module-level calibration coefficients

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

            # Get the first timestamp to calculate relative time in seconds
            initial_time = ble_utils.time_data[0]
            relative_time_data = [t - initial_time for t in ble_utils.time_data]  # Convert to seconds

            current_time = relative_time_data[-1]
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
                x=[t for t in relative_time_data if window_start <= t <= current_time],  # Use relative time for x-axis
                y=[s for t, s in zip(relative_time_data, calibrated_sensor_data) if window_start <= t <= current_time],
                mode='lines+markers',
                line=dict(color='#007BFF')
            )

        # Define the layout for the graph
        layout = go.Layout(
            xaxis=dict(range=[window_start, window_start + 10], gridcolor='#ddd', title='Time (seconds)'),  # Label x-axis
            yaxis=dict(
                range=[min(calibrated_sensor_data) - 5, max(calibrated_sensor_data) + 5],
                gridcolor='#ddd',
                title='Sensor Value (Newtons)'  # Label y-axis
            ),
            title='Live Sensor Data',
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
                return f"{float(val):.1f}"  # Limit to one decimal place
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
            Input('max-force-start-button', 'n_clicks'),
            Input('max-force-stop-button', 'n_clicks')
        ],
        [State('patient-id', 'value')]
    )
    def start_stop_recording(start_clicks, stop_clicks, patient_id):
        global current_timestamp
        start_clicks = start_clicks or 0
        stop_clicks = stop_clicks or 0
    
        print(f"Start clicks: {start_clicks}, Stop clicks: {stop_clicks}")
    
        ctx = callback_context
        if not ctx.triggered:
            return True, ""
    
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        print(f"Button clicked: {button_id}")
    
        if button_id == 'max-force-start-button':
            print(f"Patient ID: '{patient_id}'")  # Debugging statement
            if not patient_id or patient_id.strip() == "":
                print("Start recording attempted without Patient ID.")
    
                print("Attempting to close BLE connection.")
                ble_utils.close_ble_connection()
                print("BLE connection closed due to missing Patient ID.")
    
                print("Exiting function due to missing Patient ID.")
                return True, "Please enter Patient ID."
    
            print("Start recording clicked.")
    
            ble_utils.stop_event.clear()
            with ble_utils.data_lock:
                ble_utils.time_data.clear()
                ble_utils.sensor_data.clear()
                ble_utils.max_sensor_value = None
    
            ble_utils.open_ble_connection()
            print(f"BLE connection opened successfully for Patient ID: {patient_id}")
    
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
            if ble_utils.read_thread is None or not ble_utils.read_thread.is_alive():
                ble_utils.read_thread = threading.Thread(target=lambda: asyncio.run(ble_utils.read_ble_data()))
                ble_utils.read_thread.start()
                print("BLE data reading thread started.")
    
            return False, ""
    
        elif button_id == 'max-force-stop-button':
            print("Stop recording clicked.")
            ble_utils.stop_event.set()
            if ble_utils.read_thread and ble_utils.read_thread.is_alive():
                ble_utils.read_thread.join()
                print("Data reading thread joined.")
            ble_utils.close_ble_connection()
            print("BLE connection closed successfully.")
    
            return True, ""
    
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
    
            # Use current working directory as base directory
            base_dir = os.getcwd()
            print("Directory {base_dir}") # This will point to C:\Users\catha\OneDrive - University College Dublin\Desktop\Research Assistant\BLUETOOTH
            patient_folder = os.path.join(base_dir, 'profiles', sanitized_patient_id)
            os.makedirs(patient_folder, exist_ok=True)
    
            # Create a filename with the current timestamp
            filename = f'{sanitized_patient_id}_{current_timestamp}.csv'
            filepath = os.path.join(patient_folder, filename)
            df = pd.DataFrame({
                'Time (s)': [t - ble_utils.time_data[0] for t in ble_utils.time_data],  # Store relative time in CSV
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
