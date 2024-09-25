from dash import html

layout = html.Div([
    html.H1('Arcade Page', style={'textAlign': 'center', 'color': '#007BFF', 'margin-bottom': '40px'}),

    html.Div([
        html.Button('Pong', id='pong-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'}),
        html.Button('Flappy Bird', id='flappy-bird-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'}),
        html.Button('Other?', id='other-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center', 'justify-content': 'center', 'height': '60vh'})
])
