from dash import html

layout = html.Div([
    html.H1('Dashboard Menu', style={'textAlign': 'center', 'color': '#007BFF'}),
    html.Div([
        html.Button('Max Force Test', id='max-force-button', n_clicks=0, 
                    style={'width': '300px', 'height': '100px', 'font-size': '24px', 'margin': '10px'}),
        html.Button('Calibration', id='calibration-button', n_clicks=0, 
                    style={'width': '300px', 'height': '100px', 'font-size': '24px', 'margin': '10px'}),
        html.Button('Arcade', id='arcade-button', n_clicks=0, 
                    style={'width': '300px', 'height': '100px', 'font-size': '24px', 'margin': '10px'}),
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justify-content': 'center', 'height': '60vh'})
])
