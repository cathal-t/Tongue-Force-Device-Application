from dash import dcc, html

layout = html.Div([
    html.H1('Live Sensor Data Streaming', style={'textAlign': 'center', 'color': '#007BFF', 'margin-bottom': '40px'}),

    # Patient ID input
    html.Div([
        html.H3('Patient ID:', style={'color': '#333'}),
        dcc.Input(id='patient-id', type='text', placeholder='Enter Patient ID',
                  style={'width': '100%', 'padding': '10px', 'font-size': '16px', 'border': '1px solid #ccc', 'border-radius': '4px'}),
        html.Div(id='id-warning', style={'color': 'red', 'margin-top': '10px'})
    ], style={'margin-bottom': '20px'}),

    # Live data display (Current and Max Sensor Values)
    html.Div([
        html.Div([
            html.H3('Current Sensor Value:', style={'color': '#333', 'margin-bottom': '5px'}),
            html.H4(id='live-sensor-value', style={'font-size': '20px', 'font-weight': 'bold', 'color': '#28a745', 'margin': '5px 0'}),
            html.H3('Maximum Sensor Value:', style={'color': '#333', 'margin-bottom': '5px', 'margin-top': '10px'}),
            html.H4(id='max-sensor-value', style={'font-size': '20px', 'font-weight': 'bold', 'color': '#dc3545', 'margin': '5px 0'}),
        ], style={'flex': '1', 'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#fff',
                  'border-radius': '8px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)', 'display': 'flex', 'flexDirection': 'column', 'justify-content': 'center'}),

        # Display for 40%, 60%, and 80% of Max Value
        html.Div([
            html.H4('40% Max Value:', style={'font-size': '16px', 'font-weight': 'bold', 'color': '#333', 'margin-bottom': '5px'}),
            html.H4(id='forty-percent', style={'font-size': '16px', 'color': '#555', 'margin': '5px 0'}),
            html.H4('60% Max Value:', style={'font-size': '16px', 'font-weight': 'bold', 'color': '#333', 'margin-top': '5px'}),
            html.H4(id='sixty-percent', style={'font-size': '16px', 'color': '#555', 'margin': '5px 0'}),
            html.H4('80% Max Value:', style={'font-size': '16px', 'font-weight': 'bold', 'color': '#333', 'margin-top': '5px'}),
            html.H4(id='eighty-percent', style={'font-size': '16px', 'color': '#555', 'margin': '5px 0'}),
        ], style={'flex': '1', 'textAlign': 'center', 'padding': '10px', 'backgroundColor': '#fff',
                  'border-radius': '8px', 'box-shadow': '0 4px 8px rgba(0, 0, 0, 0.1)', 'display': 'flex', 'flexDirection': 'column', 'justify-content': 'center'})
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'stretch', 'margin-bottom': '40px', 'width': '500px', 'margin-left': 'auto', 'margin-right': 'auto'}),

    # Graph display for live data
    dcc.Graph(id='live-graph', config={'displayModeBar': False}),

    # Interval for real-time updates
    dcc.Interval(id='graph-update', interval=10, n_intervals=0),

    # Buttons to start/stop recording and save data
    html.Div([
        html.Button('Start Recording', id='start-button', n_clicks=0, style={'background-color': '#007BFF', 'color': '#fff', 'padding': '15px 32px', 'border': 'none', 'border-radius': '4px', 'font-size': '16px', 'margin-right': '10px'}),
        html.Button('Stop Recording', id='stop-button', n_clicks=0, style={'background-color': '#dc3545', 'color': '#fff', 'padding': '15px 32px', 'border': 'none', 'border-radius': '4px', 'font-size': '16px', 'margin-right': '10px'}),
        html.Button('Save Data to CSV', id='save-button', n_clicks=0, style={'background-color': '#28a745', 'color': '#fff', 'padding': '15px 32px', 'border': 'none', 'border-radius': '4px', 'font-size': '16px'})
    ], style={'textAlign': 'center', 'margin-top': '20px'}),

    # Confirmation message for saving data
    html.Div(id='save-confirmation', style={'margin-top': '20px', 'color': '#007BFF', 'font-size': '16px', 'textAlign': 'center'})
])
