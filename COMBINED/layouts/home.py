from dash import html, dcc

layout = html.Div([
    html.H1('Dashboard Menu', style={'textAlign': 'center', 'color': '#007BFF'}),

    # Dropdown for selecting communication method
    html.Div([
        html.Label('Select Communication Method', style={'fontSize': '20px', 'textAlign': 'center'}),
        dcc.Dropdown(
            id='comm-method-dropdown',
            options=[
                {'label': 'Serial', 'value': 'Serial'},
                {'label': 'BLE', 'value': 'BLE'}
            ],
            value='BLE',  # Default communication method
            style={'width': '300px', 'margin': 'auto'}
        ),
    ], style={'textAlign': 'center', 'margin': '20px 0'}),  # Adding some margin for spacing

    html.Div(id='comm-method-output', style={'textAlign': 'center', 'margin': '10px 0'}),

    # Existing buttons
    html.Div([
        html.Button('Max Force Test', id='max-force-button', n_clicks=0,
                    style={'width': '300px', 
                           'height': '100px', 
                           'font-size': '24px',
                           'border-radius': '18px', 
                           'margin': '10px'}),
        html.Button('Calibration', id='calibration-button', n_clicks=0,
                    style={'width': '300px', 'height': '100px', 'font-size': '24px', 'border-radius': '18px', 'margin': '10px'}),
        html.Button('Arcade', id='arcade-button', n_clicks=0,
                    style={'width': '300px', 'height': '100px', 'font-size': '24px', 'border-radius': '18px', 'margin': '10px'}),
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justify-content': 'center',
        'height': '60vh'
    })
])