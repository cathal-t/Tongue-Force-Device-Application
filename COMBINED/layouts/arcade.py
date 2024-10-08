from dash import html, dcc

layout = html.Div([
    html.H1('Arcade Page', style={'textAlign': 'center', 'color': '#007BFF', 'margin-bottom': '40px'}),

    # Display the current communication method (Serial or BLE)
    html.Div(id='arcade-comm-status', style={
        'textAlign': 'center',
        'font-size': '18px',
        'margin-bottom': '20px',
        'color': '#555'
    }),

    # Buttons to launch arcade games
    html.Div([
        html.Button('Pong', id='pong-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'}),
        html.Button('Flappy Bird', id='flappy-bird-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'}),
        html.Button('Other?', id='other-button', n_clicks=0,
                    style={'width': '200px', 'height': '50px', 'font-size': '20px', 'margin': '10px'})
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'alignItems': 'center',
        'justify-content': 'center',
        'height': '60vh'
    }),

    # Hidden confirmation message after launching the game
    html.Div(id='game-launch-confirmation', style={
        'textAlign': 'center',
        'font-size': '16px',
        'color': '#28a745',
        'margin-top': '20px',
        'display': 'none'  # Initially hidden
    }),

    # Interval for periodic updates if needed
    dcc.Interval(id='arcade-status-update', interval=1000, n_intervals=0)
])
