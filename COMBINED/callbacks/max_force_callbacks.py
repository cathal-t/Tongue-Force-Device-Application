from dash import Input, Output, State, callback_context, html, dcc  # Added dcc for Location component
import dash_bootstrap_components as dbc
import threading
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
            x=[t for t in relative_time_data if window_start <= t <= current_time],
            y=[s for t, s in zip(relative_time_data, calibrated_sensor_data) if window_start <= t <= current_time],
            mode='lines+markers',
            line=dict(color='#007BFF')
        )

        # Define the layout for the graph
        layout = go.Layout(
            xaxis=dict(
                range=[window_start, window_start + 10],
                gridcolor='#ddd',
                title='Time (seconds)',
                titlefont=dict(size=18),
                tickfont=dict(size=14)
            ),
            yaxis=dict(
                range=[min(calibrated_sensor_data) - 5, max(calibrated_sensor_data) + 5],
                gridcolor='#ddd',
                title='Sensor Value (Newtons)',
                titlefont=dict(size=18),
                tickfont=dict(size=14)
            ),
            title='Live Sensor Data (Calibrated to Newtons)',
            titlefont=dict(size=24),
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

    # Combined Callback to handle start/stop recording and saving data
    @app.callback(
        [
            Output('graph-update', 'disabled'),
            Output('id-warning', 'children'),
            Output('save-data-modal', 'is_open'),
            Output('unsaved-data-flag', 'data'),
            Output('save-confirmation', 'children')
        ],
        [
            Input('max-force-start-button', 'n_clicks'),
            Input('max-force-stop-button', 'n_clicks'),
            Input('modal-dont-save-button', 'n_clicks'),
            Input('modal-save-button', 'n_clicks')
        ],
        [
            State('patient-id', 'value'),
            State('unsaved-data-flag', 'data'),
            State('save-data-modal', 'is_open'),
            State('shared-calibration-coefficients', 'data')
        ]
    )
    def handle_recording_and_saving(start_clicks, stop_clicks, modal_dont_save_clicks, modal_save_clicks,
                                    patient_id, unsaved_data, is_modal_open, calibration_coefficients):
        global current_timestamp
        ctx = callback_context
        if not ctx.triggered:
            # Initial state
            return True, "", False, unsaved_data, ""

        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == 'max-force-start-button':
            if unsaved_data:
                # Prevent starting a new session if there is unsaved data
                return True, "Please save or discard the current data before starting a new recording.", is_modal_open, unsaved_data, ""
            if not patient_id or patient_id.strip() == "":
                # Do not close the connection; just show warning
                return True, "Please enter Patient ID.", is_modal_open, unsaved_data, ""

            # Start reading data
            comm_handler.clear_data()
            current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Start reading (this will handle connecting if necessary)
            comm_handler.start_reading()

            return False, "", is_modal_open, unsaved_data, ""

        elif triggered_id == 'max-force-stop-button':
            # Open the modal immediately
            unsaved_data = True
            is_modal_open = True

            # Stop reading data (stop notifications)
            comm_handler.stop_reading()

            return True, "", is_modal_open, unsaved_data, ""

        elif triggered_id == 'modal-dont-save-button':
            # User chose not to save data
            # Clear data
            comm_handler.clear_data()
            # Close the modal
            unsaved_data = False
            return True, "", False, unsaved_data, ""

        elif triggered_id == 'modal-save-button':
            # User chose to save data
            if unsaved_data:
                time_data = comm_handler.get_time_data()
                sensor_data = comm_handler.get_sensor_data()
                if not time_data:
                    return True, "", False, False, "No data to save. Please record data first."
                if not current_timestamp:
                    current_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

                # Extract calibration coefficients
                calibration_slope = calibration_coefficients.get('slope', 1) if calibration_coefficients else 1
                calibration_intercept = calibration_coefficients.get('intercept', 0) if calibration_coefficients else 0

                # Sanitize patient_id to remove invalid characters
                sanitized_patient_id = re.sub(r'[^A-Za-z0-9_\- ]+', '', patient_id)
                if not sanitized_patient_id:
                    return True, "", False, False, "Invalid Patient ID."

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
                    return True, "", False, False, f"Error saving data: {e}"

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
                        stats_file.write(f'Calibration Slope: {calibration_slope}\n')
                        stats_file.write(f'Calibration Intercept: {calibration_intercept}\n')
                except Exception as e:
                    return True, "", False, False, f"Error saving statistics: {e}"

                # Clear the data after saving
                comm_handler.clear_data()

                # Reset unsaved_data flag and close modal
                unsaved_data = False
                save_confirmation_message = f'Data saved to {filepath} and statistics saved to {stats_filepath}'
                return True, "", False, unsaved_data, save_confirmation_message
            else:
                return True, "", False, unsaved_data, ""

        else:
            return True, "", is_modal_open, unsaved_data, ""

    # Callback to detect page navigation and close BLE connection
    @app.callback(
        Output('dummy-output', 'children'),
        [Input('url', 'pathname')]
    )
    def close_ble_connection_on_page_exit(pathname):
        if pathname != '/max-force-test':
            comm_handler.close_connection()
        return ''
