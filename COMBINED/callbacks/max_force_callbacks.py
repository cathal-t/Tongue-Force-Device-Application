from dash import Input, Output, State, callback_context, html
from datetime import datetime
import pandas as pd
import plotly.graph_objs as go
import os
import re
from utils.communication_utils import comm_handler  # Use the generic communication handler

# Initialize current timestamp
current_timestamp = None

def register_callbacks(app):
    # Callback to monitor and update communication connection status
    @app.callback(
        Output('connection-status', 'children'),
        [Input('graph-update', 'n_intervals')]
    )
    def update_connection_status(n):
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

    # Callback for updating the live graph and sensor values
    @app.callback(
        Output('live-graph', 'figure'),
        [Input('graph-update', 'n_intervals')],
        [State('shared-calibration-coefficients', 'data')]
    )
    def update_graph(n, calibration_coefficients):
        time_data = comm_handler.get_time_data()
        sensor_data = comm_handler.get_sensor_data()
        if len(time_data) == 0 or len(sensor_data) == 0:
            return go.Figure()

        # Get the first timestamp to calculate relative time in seconds
        initial_time = time_data[0]
        relative_time_data = [t - initial_time for t in time_data]  # Convert to seconds

        current_time = relative_time_data[-1]
        window_start = max(0, current_time - 10)

        # Extract calibration coefficients
        calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
        calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

        # Apply calibration to the sensor values
        calibrated_sensor_data = [calibration_slope * s + calibration_intercept for s in sensor_data]

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
        sensor_data = comm_handler.get_sensor_data()
        max_sensor_value = comm_handler.get_max_sensor_value()
        if not sensor_data:
            return "N/A", "N/A", "N/A", "N/A", "N/A"

        # Extract calibration coefficients
        calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
        calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

        # Apply calibration to the current sensor value and max value
        current_value = calibration_slope * sensor_data[-1] + calibration_intercept
        current_max_sensor_value = (
            calibration_slope * max_sensor_value + calibration_intercept
            if max_sensor_value is not None else None
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
            return f"{float(val):.1f}" if isinstance(val, (int, float)) else "N/A"

        return (
            f"{format_value(current_value)} N",
            f"{format_value(current_max_sensor_value)} N",
            format_value(forty_percent),
            format_value(sixty_percent),
            format_value(eighty_percent)
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

        ctx = callback_context
        if not ctx.triggered:
            return True, ""

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'max-force-start-button':
            if not patient_id or patient_id.strip() == "":
                comm_handler.close_connection()
                return True, "Please enter Patient ID."

            # Clear data ONLY when starting a new recording
            comm_handler.clear_data()

            # Start reading data
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            comm_handler.start_reading()

            return False, ""  # Disable the start button, enable the stop button

        elif button_id == 'max-force-stop-button':
            # Stop reading data
            comm_handler.stop_reading()

            return True, ""  # Enable the start button again

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
            time_data = comm_handler.get_time_data()
            sensor_data = comm_handler.get_sensor_data()
            if not time_data:
                return "No data to save. Please record data first."
            if not current_timestamp:
                current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Extract calibration coefficients
            calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
            calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

            # Sanitize patient_id to remove invalid characters
            sanitized_patient_id = re.sub(r'[^A-Za-z0-9_\- ]+', '', patient_id)
            if not sanitized_patient_id:
                return "Invalid Patient ID."
            
            # Create the patient's folder inside the 'profiles' directory
            patient_folder = os.path.join('profiles', sanitized_patient_id)
            os.makedirs(patient_folder, exist_ok=True)

            # Convert absolute time to relative time
            initial_time = time_data[0]  # Reference timestamp (first recorded time)
            relative_time_data = [t - initial_time for t in time_data]  # Relative time in seconds

            # Create a filename with the current timestamp
            filename = f'{sanitized_patient_id}_{current_timestamp}.csv'
            filepath = os.path.join(patient_folder, filename)

            # Create DataFrame with relative time and calibrated sensor values
            df = pd.DataFrame({
                'Time (s)': relative_time_data,  # Use relative time in seconds
                'Sensor Value (Newtons)': [
                    calibration_slope * s + calibration_intercept for s in sensor_data
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
