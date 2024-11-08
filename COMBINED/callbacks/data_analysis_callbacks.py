# callbacks/data_analysis_callbacks.py

from dash import Input, Output, State, callback_context, dcc
from dash.exceptions import PreventUpdate
import plotly.graph_objs as go
import pandas as pd
from utils.data_utils import get_patient_ids, get_sessions_for_patient
import os

def register_callbacks(app):
    @app.callback(
        Output('patient-id-dropdown', 'options'),
        [Input('url', 'pathname')]
    )
    def update_patient_dropdown(pathname):
        if pathname != '/data-analysis':
            raise PreventUpdate
        patient_ids = get_patient_ids()
        return [{'label': pid, 'value': pid} for pid in patient_ids]

    @app.callback(
        Output('session-checklist', 'options'),
        [Input('patient-id-dropdown', 'value')]
    )
    def update_session_checklist(patient_id):
        if not patient_id:
            return []
        sessions = get_sessions_for_patient(patient_id)
        return sessions

    @app.callback(
        Output('time-range-slider', 'min'),
        Output('time-range-slider', 'max'),
        Output('time-range-slider', 'value'),
        Output('time-range-slider', 'marks'),
        Output('time-range-slider', 'disabled'),
        [Input('session-checklist', 'value')],
        [State('patient-id-dropdown', 'value')]
    )
    def update_time_range_slider(selected_sessions, patient_id):
        if not patient_id or not selected_sessions:
            return 0, 10, [0, 10], {0: '0', 10: '10'}, True  # Disabled slider

        min_time = float('inf')
        max_time = float('-inf')

        for session_file in selected_sessions:
            session_path = os.path.join('profiles', patient_id, session_file)
            if not os.path.exists(session_path):
                continue
            df = pd.read_csv(session_path)
            session_min_time = df['Time (s)'].min()
            session_max_time = df['Time (s)'].max()
            min_time = min(min_time, session_min_time)
            max_time = max(max_time, session_max_time)

        if min_time == float('inf') or max_time == float('-inf'):
            return 0, 10, [0, 10], {0: '0', 10: '10'}, True  # Disabled slider

        marks = {int(min_time): str(int(min_time)), int(max_time): str(int(max_time))}
        value = [min_time, max_time]

        return min_time, max_time, value, marks, False  # Enabled slider

    @app.callback(
        Output('data-analysis-graph', 'figure'),
        [Input('plot-data-button', 'n_clicks')],
        [
            State('patient-id-dropdown', 'value'),
            State('session-checklist', 'value'),
            State('time-range-slider', 'value'),  # Added time range state
        ]
    )

    def update_graph(n_clicks, patient_id, selected_sessions, time_range):
        if not n_clicks or not patient_id or not selected_sessions:
            raise PreventUpdate

        data_traces = []
        for session_file in selected_sessions:
            session_path = os.path.join('profiles', patient_id, session_file)
            if not os.path.exists(session_path):
                continue
            df = pd.read_csv(session_path)
            # Filter data based on time range
            if time_range:
                df = df[(df['Time (s)'] >= time_range[0]) & (df['Time (s)'] <= time_range[1])]
            trace = go.Scatter(
                x=df['Time (s)'],
                y=df['Sensor Value (Newtons)'],
                mode='lines',
                name=session_file
            )
            data_traces.append(trace)

        if not data_traces:
            return go.Figure()

        layout = go.Layout(
            title='',
            xaxis=dict(
                title='Time (s)',
                titlefont=dict(size=22),    # Increase font size for the x-axis title
                tickfont=dict(size=16), 
                showgrid=True,
                showline=True,
                linewidth=2,      # Set line width for the axis
                linecolor='black' # Color for the y-axis line
            ),
            yaxis=dict(
                title='Force (N)',
                titlefont=dict(size=22),    # Increase font size for the x-axis title
                tickfont=dict(size=16), 
                showgrid=True,
                showline=True,
                linewidth=2,      # Set line width for the axis
                linecolor='black' # Color for the y-axis line
            ),
            hovermode='closest',
            plot_bgcolor='white',  # Change the background of the plot area
            paper_bgcolor='white'  # Change the background of the entire chart
        )

        fig = go.Figure(data=data_traces, layout=layout)
        return fig

    # Callback for exporting the plot
    @app.callback(
        Output('download-image', 'data'),  # Use dcc.Download component
        [
            Input('export-png-button', 'n_clicks'),
            Input('export-jpeg-button', 'n_clicks'),
            Input('export-pdf-button', 'n_clicks')
        ],
        [State('data-analysis-graph', 'figure')]
    )
    def export_plot(png_clicks, jpeg_clicks, pdf_clicks, figure):
        ctx = callback_context
        if not ctx.triggered or not figure:
            raise PreventUpdate

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        if button_id == 'export-png-button':
            format = 'png'
            filename = 'plot.png'
        elif button_id == 'export-jpeg-button':
            format = 'jpeg'
            filename = 'plot.jpeg'
        elif button_id == 'export-pdf-button':
            format = 'pdf'
            filename = 'plot.pdf'
        else:
            raise PreventUpdate

        import io
        import plotly.io as pio

        img_bytes = pio.to_image(figure, format=format)
        return dict(content=img_bytes, filename=filename)
