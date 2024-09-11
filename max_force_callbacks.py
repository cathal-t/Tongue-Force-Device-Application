from dash import Input, Output, State
from datetime import datetime
import pandas as pd
import threading
import plotly.graph_objs as go
import os
import sys
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.serial_utils import open_serial_port, close_serial_port, read_serial_data, stop_event, time_data, sensor_data, max_sensor_value, read_thread, data_lock

# Load the calibration coefficients safely
try:
    with open(os.path.join(os.path.dirname(__file__), '..', 'calibration_data.txt'), 'r') as f:
        data = f.read().strip()  # Strip any extra spaces or newlines
        if data:
            calibration_slope, calibration_intercept = map(float, data.split(','))
        else:
            raise ValueError("Empty calibration data")
except (FileNotFoundError, ValueError):
    # Use default calibration if the file is not found or data is invalid
    calibration_slope, calibration_intercept = 1, 0
    print("Warning: Calibration data not found or invalid. Using default values.")

# Callback for updating the live graph and sensor values
def register_callbacks(app):
    @app.callback(
        Output('live-graph', 'figure'),
        [Input('graph-update', 'n_intervals')]
    )
    def update_graph(n):
        # Acquire lock before accessing shared data
        with data_lock:
            if len(time_data) == 0:
                return go.Figure()

            current_time = time_data[-1]
            window_start = max(0, current_time - 10)

            # Apply calibration to the sensor values
            calibrated_sensor_data = [calibration_slope * s + calibration_intercept for s in sensor_data]

            # Prepare data for the live graph with calibrated values
            data = go.Scatter(
                x=[t for t in time_data if window_start <= t <= current_time],
                y=[s for t, s in zip(time_data, calibrated_sensor_data) if window_start <= t <= current_time],
                mode='lines+markers',
                line=dict(color='#007BFF')
            )

        # Define the layout for the graph with calibrated y-axis range (based on expected Newton range)
        layout = go.Layout(
            xaxis=dict(range=[window_start, window_start + 10], gridcolor='#ddd'),
            yaxis=dict(range=[min(calibrated_sensor_data) - 5, max(calibrated_sensor_data) + 5], gridcolor='#ddd'),
            title='Live Sensor Data (Calibrated to Newtons)',
            plot_bgcolor='#fff',
            paper_bgcolor='#f4f4f4',
            font=dict(color='#333'),
            margin=dict(l=40, r=40, t=50, b=40),
        )

        return {'data': [data], 'layout': layout}

    # Callback for live sensor value, max value, and percentages
    @app.callback(
        [Output('live-sensor-value', 'children'),
         Output('max-sensor-value', 'children'),
         Output('forty-percent', 'children'),
         Output('sixty-percent', 'children'),
         Output('eighty-percent', 'children')],
        [Input('graph-update', 'n_intervals')]
    )
    def update_live_and_max_value(n):
        # Acquire lock before accessing shared data
        with data_lock:
            if not sensor_data:
                return "N/A", "N/A", "N/A", "N/A", "N/A"

            # Apply calibration to the current sensor value and max value
            current_value = calibration_slope * sensor_data[-1] + calibration_intercept
            current_max_sensor_value = calibration_slope * max_sensor_value + calibration_intercept if max_sensor_value is not None else "N/A"
            
            # Calculate percentages of the max value (if valid)
            if isinstance(current_max_sensor_value, float):
                forty_percent = current_max_sensor_value * 0.4
                sixty_percent = current_max_sensor_value * 0.6
                eighty_percent = current_max_sensor_value * 0.8
            else:
                forty_percent, sixty_percent, eighty_percent = "N/A", "N/A", "N/A"

        return f"{current_value:.2f} N", f"{current_max_sensor_value:.2f} N", f"{forty_percent:.2f}", f"{sixty_percent:.2f}", f"{eighty_percent:.2f}"

    # Callback to start/stop recording
    @app.callback(
        [Output('graph-update', 'disabled'),
         Output('id-warning', 'children')],
        [Input('start-button', 'n_clicks'),
         Input('stop-button', 'n_clicks')],
        [State('patient-id', 'value')]
    )
    def start_stop_recording(start_clicks, stop_clicks, patient_id):
        global read_thread, current_timestamp
        
        # Start recording logic
        if start_clicks > stop_clicks:
            if not patient_id:
                return True, "Please enter Patient ID."
    
            # Clear stop_event to allow the thread to start
            stop_event.clear()
    
            # Clear any existing data points for a fresh start
            time_data.clear()
            sensor_data.clear()
    
            # Open the serial port and reset buffer
            try:
                open_serial_port()
                serial_port.reset_input_buffer()  # Clear any stale data in the buffer
            except Exception as e:
                print(f"Error opening serial port: {e}")
                return True, f"Error: Could not open serial port."
    
            # Generate a unique timestamp for the current recording session
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
            # Start a new thread to read serial data
            if read_thread is None or not read_thread.is_alive():
                read_thread = threading.Thread(target=read_serial_data)
                read_thread.start()
    
            # Enable graph updates and clear warnings
            return False, ""
    
        # Stop recording logic
        else:
            # Signal the thread to stop reading
            stop_event.set()
    
            # Add a small delay to ensure proper stopping of the thread
            time.sleep(0.1)
    
            # Ensure the thread is properly terminated
            if read_thread is not None:
                read_thread.join(timeout=1)  # Allow the thread to terminate
    
            # Close the serial port, handle exceptions
            try:
                if serial_port.is_open:
                    close_serial_port()
            except Exception as e:
                print(f"Error closing serial port: {e}")
                return True, f"Error: Could not close serial port."
    
            # Disable graph updates and clear warnings
            return True, ""




    # Callback to save the data to a CSV file
    @app.callback(
        Output('save-confirmation', 'children'),
        [Input('save-button', 'n_clicks')],
        [State('patient-id', 'value')]
    )
    def save_data_to_csv(n_clicks, patient_id):
        if n_clicks > 0 and patient_id:
            # Create a filename with the current timestamp
            filename = f'{patient_id}_{current_timestamp}.csv'
            df = pd.DataFrame({
                'Time (s)': time_data,
                'Sensor Value (Newtons)': [calibration_slope * s + calibration_intercept for s in sensor_data]
            })
            df.to_csv(filename, index=False)
            return f'Data saved to {filename}'
        return ""