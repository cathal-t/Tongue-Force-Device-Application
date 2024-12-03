# callbacks/recording_callbacks.py

from dash import Input, Output, State, callback_context, html, dcc
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from datetime import datetime
import pandas as pd
import plotly.graph_objs as go
import os
import re
from utils.communication_utils import comm_handler

# Initialize current timestamp
current_timestamp = None

def register_callbacks(app):
    # Callback to update patient ID dropdown options
    @app.callback(
        Output('recording-patient-id-dropdown', 'options'),
        [Input('url', 'pathname')]
    )
    def update_patient_dropdown(pathname):
        if pathname != '/recording':
            return []
        patient_ids = get_patient_ids()
        return [{'label': pid, 'value': pid} for pid in patient_ids]

    # Callback to update session checklist options based on selected patient ID
    @app.callback(
        Output('recording-session-checklist', 'options'),
        [Input('recording-patient-id-dropdown', 'value')]
    )
    def update_session_checklist(patient_id):
        if not patient_id:
            return []
        sessions = get_statistics_files_for_patient(patient_id)
        return sessions

    # Helper function to get patient IDs
    def get_patient_ids():
        profiles_dir = os.path.join(os.path.dirname(__file__), '..', 'profiles')
        patient_ids = []
        if os.path.exists(profiles_dir):
            for name in os.listdir(profiles_dir):
                full_path = os.path.join(profiles_dir, name)
                if os.path.isdir(full_path):
                    patient_ids.append(name)
        return patient_ids

    # Helper function to get statistics files for a patient
    def get_statistics_files_for_patient(patient_id):
        patient_dir = os.path.join(os.path.dirname(__file__), '..', 'profiles', patient_id)
        stats_files = []
        if os.path.exists(patient_dir):
            for file in os.listdir(patient_dir):
                if file.startswith('statistics_') and file.endswith('.txt'):
                    stats_files.append({'label': file, 'value': file})
        return stats_files

    # Callback to monitor and update communication connection status
    @app.callback(
        Output('recording-connection-status', 'children'),
        [Input('recording-connection-interval', 'n_intervals')]
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
            return html.Div("")

    # Helper function to read percentage values from the statistics file
    import re

    def read_percentage_values(stats_file_path):
        percentage_values = {}
        try:
            with open(stats_file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if 'Calibration' in line:
                        continue  # Skip calibration lines
                    # Match lines like 'Max Force: value N'
                    max_force_match = re.match(r'Max Force\s*:\s*([0-9.]+)', line)
                    if max_force_match:
                        value = float(max_force_match.group(1))
                        percentage_values['Max Force'] = value
                        continue
                    # Match lines like '20% of Max Force: value N' or '20% Max Force: value N'
                    percent_match = re.match(r'(\d+)%.*Max Force\s*:\s*([0-9.]+)', line)
                    if percent_match:
                        percent_label = percent_match.group(1) + '%'
                        value = float(percent_match.group(2))
                        percentage_values[percent_label] = value
        except Exception as e:
            print(f"Error reading statistics file: {e}")
        return percentage_values

    # Callback for updating the live graph and sensor values
    @app.callback(
        Output('recording-live-graph', 'figure'),
        [Input('recording-graph-update', 'n_intervals')],
        [
            State('shared-calibration-coefficients', 'data'),
            State('recording-patient-id-dropdown', 'value'),
            State('recording-session-checklist', 'value')
        ]
    )
    def update_graph(n, calibration_coefficients, selected_patient_id, selected_sessions):
        time_data = comm_handler.get_time_data()
        sensor_data = comm_handler.get_sensor_data()
        if len(time_data) == 0 or len(sensor_data) == 0:
            return go.Figure()

        # Get the first timestamp to calculate relative time in seconds
        initial_time = time_data[0]
        relative_time_data = [t - initial_time for t in time_data]  # Convert to seconds

        current_time = relative_time_data[-1]
        window_start = max(0, current_time - 10)
        window_end = current_time + 3

        # Extract calibration coefficients
        calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
        calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

        # Apply calibration to the sensor values
        calibrated_sensor_data = [calibration_slope * s + calibration_intercept for s in sensor_data]

        if not calibrated_sensor_data:
            return go.Figure()

        # Prepare data for the live graph with calibrated values
        data = go.Scatter(
            x=[t for t in relative_time_data if window_start <= t <= window_end],
            y=[s for t, s in zip(relative_time_data, calibrated_sensor_data) if window_start <= t <= window_end],
            mode='lines+markers',
            line=dict(color='#007BFF'),
            name='Live Sensor Data'
        )

        # Initialize shapes, annotations, and max force values
        shapes = []
        annotations = []
        max_upper_bound = 0  # For computing y_max

        # Define the colors for each zone
        zone_colors = {
            '20%': 'rgba(255, 0, 0, 0.2)',       # Red
            '40%': 'rgba(255, 165, 0, 0.2)',     # Orange
            '60%': 'rgba(255, 255, 0, 0.2)',     # Yellow
            '80%': 'rgba(0, 128, 0, 0.2)',       # Green
        }

        # If sessions are selected, read the percentage values and add zones
        percentage_values = {}
        if selected_patient_id and selected_sessions:
            profiles_dir = os.path.join(os.path.dirname(__file__), '..', 'profiles')
            for stats_file in selected_sessions:
                stats_file_path = os.path.join(profiles_dir, selected_patient_id, stats_file)
                if os.path.exists(stats_file_path):
                    file_percentage_values = read_percentage_values(stats_file_path)
                    percentage_values.update(file_percentage_values)

        # Create shapes for each zone
        for percent_label in ['20%', '40%', '60%', '80%']:
            if percent_label in percentage_values:
                value = percentage_values[percent_label]
                lower_bound = value -5
                upper_bound = value +5
                # Update max_upper_bound
                if upper_bound > max_upper_bound:
                    max_upper_bound = upper_bound
                shapes.append({
                    'type': 'rect',
                    'xref': 'x',
                    'yref': 'y',
                    'x0': window_start,
                    'y0': lower_bound,
                    'x1': window_end,
                    'y1': upper_bound,
                    'fillcolor': zone_colors.get(percent_label, 'rgba(0,0,0,0.1)'),
                    'opacity': 0.4,
                    'layer': 'below',
                    'line': {
                        'width': 0,
                    },
                })
                annotations.append({
                    'x': window_start + (window_end - window_start) / 2 + 1,
                    'y': value,
                    'xref': 'x',
                    'yref': 'y',
                    'text': f"{percent_label} Target",
                    'showarrow': False,
                    'font': {'size':20, 'color': '#000'}
                })

        # Determine the y-axis range
        if max_upper_bound > 0:
            y_max = max_upper_bound + (0.2 * max_upper_bound)  # Add 20% buffer
            y_min = -10  # Assuming minimum force is zero
        else:
            y_max = max(calibrated_sensor_data) + 5
            y_min = min(calibrated_sensor_data) - 5

        # Define the layout for the graph with the new y-axis range and shapes
        layout = go.Layout(
            xaxis=dict(
                range=[window_start, window_end],
                gridcolor='#ddd',
                title='Time (seconds)',
                titlefont=dict(size=18),
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                range=[y_min, y_max],
                gridcolor='#ddd',
                title='Sensor Value (Newtons)',
                titlefont=dict(size=18),
                tickfont=dict(size=14)
            ),
            title=' ',
            titlefont=dict(size=24),
            plot_bgcolor='#fff',
            paper_bgcolor='#f4f4f4',
            font=dict(color='#333'),
            margin=dict(l=40, r=40, t=50, b=40),
            shapes=shapes,
            annotations=annotations,
        )

        return {'data': [data], 'layout': layout}

    # Callback for live sensor value and max value
    @app.callback(
        [
            Output('recording-live-sensor-value', 'children'),
            Output('recording-max-sensor-value', 'children'),
            Output('recording-file-warning', 'children')  # Correct Output ID
        ],
        [Input('recording-graph-update', 'n_intervals')],
        [
            State('shared-calibration-coefficients', 'data'),
            State('recording-patient-id-dropdown', 'value'),
            State('recording-session-checklist', 'value')
        ]
    )
    def update_live_and_max_value(n, calibration_coefficients, selected_patient_id, selected_sessions):
        sensor_data = comm_handler.get_sensor_data()
        max_sensor_value = comm_handler.get_max_sensor_value()
        if not sensor_data:
            return "N/A", "N/A", ""

        # Extract calibration coefficients
        calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
        calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

        # Apply calibration to the current sensor value and max value
        current_value = calibration_slope * sensor_data[-1] + calibration_intercept
        current_max_sensor_value = (
            calibration_slope * max_sensor_value + calibration_intercept
            if max_sensor_value is not None else None
        )

        # Check if a statistics file is selected
        if not selected_patient_id or not selected_sessions:
            file_warning = "Please select a patient and at least one statistics file."
        else:
            file_warning = ""

        # Format the output strings
        def format_value(val):
            return f"{float(val):.1f}" if isinstance(val, (int, float)) else "N/A"

        return (
            f"{format_value(current_value)} N",
            f"{format_value(current_max_sensor_value)} N",
            file_warning
        )

    # Combined Callback to handle start/stop recording and saving data
    @app.callback(
        [
            Output('recording-graph-update', 'disabled'),
            Output('recording-id-warning', 'children'),
            Output('recording-save-data-modal', 'is_open'),
            Output('recording-unsaved-data-flag', 'data'),
            Output('recording-save-confirmation', 'children'),
            Output('recording-file-warning-start', 'children')  # Updated Output ID
        ],
        [
            Input('recording-start-button', 'n_clicks'),
            Input('recording-stop-button', 'n_clicks'),
            Input('recording-modal-dont-save-button', 'n_clicks'),
            Input('recording-modal-save-button', 'n_clicks')
        ],
        [
            State('recording-unsaved-data-flag', 'data'),
            State('recording-save-data-modal', 'is_open'),
            State('shared-calibration-coefficients', 'data'),
            State('recording-patient-id-dropdown', 'value'),
            State('recording-session-checklist', 'value')
        ]
    )
    def handle_recording_and_saving(start_clicks, stop_clicks, modal_dont_save_clicks, modal_save_clicks,
                                    unsaved_data, is_modal_open, calibration_coefficients,
                                    selected_patient_id, selected_sessions):
        global current_timestamp
        ctx = callback_context
        if not ctx.triggered:
            # Initial state
            return True, "", False, unsaved_data, "", ""

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == 'recording-start-button':
            if unsaved_data:
                warning_message = "Please save or discard the current data before starting a new recording."
                return True, "", is_modal_open, unsaved_data, "", warning_message
            if not selected_patient_id:
                warning_message = "Please select Patient ID."
                return True, warning_message, is_modal_open, unsaved_data, "", ""
            if not selected_sessions:
                warning_message = "Please select at least one statistics file."
                return True, "", is_modal_open, unsaved_data, "", warning_message

            # Start reading data
            comm_handler.clear_data()
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Start reading (this will handle connecting if necessary)
            comm_handler.start_reading()

            return False, "", is_modal_open, unsaved_data, "", ""

        elif triggered_id == 'recording-stop-button':
            # Open the modal immediately
            unsaved_data = True
            is_modal_open = True

            # Stop reading data (stop notifications)
            comm_handler.stop_reading()

            return True, "", is_modal_open, unsaved_data, "", ""

        elif triggered_id == 'recording-modal-dont-save-button':
            # User chose not to save data
            # Clear data
            comm_handler.clear_data()
            # Close the modal
            unsaved_data = False
            return True, "", False, unsaved_data, "", ""

        elif triggered_id == 'recording-modal-save-button':
            # User chose to save data
            if unsaved_data:
                time_data = comm_handler.get_time_data()
                sensor_data = comm_handler.get_sensor_data()
                if not time_data:
                    return True, "", False, False, "No data to save. Please record data first.", ""
                if not current_timestamp:
                    current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Extract calibration coefficients
                calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
                calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

                # Sanitize patient_id to remove invalid characters
                sanitized_patient_id = re.sub(r'[^A-Za-z0-9_\- ]+', '', selected_patient_id)
                if not sanitized_patient_id:
                    return True, "", False, False, "Invalid Patient ID.", ""

                # Create the patient's folder inside the 'profiles' directory
                patient_folder = os.path.join('profiles', sanitized_patient_id)
                os.makedirs(patient_folder, exist_ok=True)

                # Convert absolute time to relative time
                initial_time = time_data[0]
                relative_time_data = [t - initial_time for t in time_data]

                # Create a filename with the current timestamp
                filename = f'{sanitized_patient_id}_{current_timestamp}.csv'
                filepath = os.path.join(patient_folder, filename)

                # Create DataFrame with relative time and calibrated sensor values
                df = pd.DataFrame({
                    'Time (s)': relative_time_data,
                    'Sensor Value (Newtons)': [
                        calibration_slope * s + calibration_intercept for s in sensor_data
                    ]
                })

                try:
                    df.to_csv(filepath, index=False)
                except Exception as e:
                    return True, "", False, False, f"Error saving data: {e}", ""

                # Clear the data after saving
                comm_handler.clear_data()

                # Reset unsaved_data flag and close modal
                unsaved_data = False
                save_confirmation_message = f'Data saved to {filepath}'
                return True, "", False, unsaved_data, save_confirmation_message, ""
            else:
                return True, "", False, unsaved_data, "", ""

        else:
            return True, "", is_modal_open, unsaved_data, "", ""

    # Callback to detect page navigation and close BLE connection
    @app.callback(
        Output('recording-dummy-output', 'children'),
        [Input('url', 'pathname')]
    )
    def close_ble_connection_on_page_exit(pathname):
        if pathname != '/recording':
            comm_handler.close_connection()
        return ''
