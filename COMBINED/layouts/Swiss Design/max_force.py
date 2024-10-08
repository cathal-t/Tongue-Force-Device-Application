from dash import dcc, html

# Common styles
font_family = 'Helvetica, Arial, sans-serif'
box_style = {
    'flex': '1',
    'textAlign': 'center',
    'padding': '20px',
    'backgroundColor': '#f8f8f8',
    'border-radius': '8px',
    'margin': '0 10px',
    'display': 'flex',
    'flexDirection': 'column',
    'justifyContent': 'center',
    'font-family': font_family
}
heading_style = {
    'color': '#000',
    'margin-bottom': '5px',
    'font-family': font_family
}
value_style = {
    'font-size': '24px',
    'font-weight': 'bold',
    'color': '#000',
    'margin': '5px 0',
    'font-family': font_family
}

layout = html.Div([
    html.H1('Live Sensor Data Streaming', style={
        'textAlign': 'center',
        'color': '#000',
        'margin-bottom': '40px',
        'font-family': font_family
    }),

    # Connection Status
    html.Div(id='connection-status', style={
        'color': '#000',
        'font-size': '18px',
        'textAlign': 'center',
        'margin-bottom': '20px',
        'font-family': font_family
    }),

    # Patient ID input
    html.Div([
        html.H3('Patient ID:', style={'color': '#000', 'font-family': font_family}),
        dcc.Input(
            id='patient-id',
            type='text',
            placeholder='Enter Patient ID',
            style={
                'width': '100%',
                'padding': '12px',
                'font-size': '16px',
                'border': '1px solid #ccc',
                'border-radius': '4px',
                'background-color': '#fff',
                'font-family': font_family
            }
        ),
        html.Div(id='id-warning', style={
            'color': 'red',
            'margin-top': '10px',
            'font-family': font_family
        })
    ], style={
        'margin-bottom': '30px',
        'padding': '20px',
        'border-radius': '8px',
        'background-color': '#f8f8f8',
        'width': '60%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'font-family': font_family
    }),

    # Live data display (Current Sensor Value, Max Sensor Value, Percentages)
    html.Div([
        # Current Sensor Value
        html.Div([
            html.H3('Current Sensor Value:', style=heading_style),
            html.H4(id='live-sensor-value', style=value_style),
        ], style=box_style),

        # Max Sensor Value
        html.Div([
            html.H3('Maximum Sensor Value:', style=heading_style),
            html.H4(id='max-sensor-value', style=value_style),
        ], style=box_style),

        # Percentages
        html.Div([
            html.H4('40% Max Value:', style={**heading_style, 'font-size': '18px'}),
            html.H4(id='forty-percent', style={**value_style, 'font-size': '18px'}),
            html.H4('60% Max Value:', style={**heading_style, 'font-size': '18px', 'margin-top': '10px'}),
            html.H4(id='sixty-percent', style={**value_style, 'font-size': '18px'}),
            html.H4('80% Max Value:', style={**heading_style, 'font-size': '18px', 'margin-top': '10px'}),
            html.H4(id='eighty-percent', style={**value_style, 'font-size': '18px'}),
        ], style=box_style),
    ], style={
        'display': 'flex',
        'justify-content': 'space-around',
        'align-items': 'stretch',
        'margin-bottom': '40px',
        'width': '85%',
        'margin-left': 'auto',
        'margin-right': 'auto',
    }),

    # Graph display for live data
    html.Div(
        dcc.Graph(id='live-graph', config={'displayModeBar': False}, style={
            'margin-bottom': '40px',
            'border-radius': '8px'
        }),
        style={
            'width': '85%',
            'margin-left': 'auto',
            'margin-right': 'auto',
        }
    ),

    # Interval for real-time updates
    dcc.Interval(id='graph-update', interval=100, n_intervals=0),

    # Buttons to start/stop recording and save data
    html.Div([
        html.Button('Start Recording', id='max-force-start-button', n_clicks=0, style={
            'background-color': '#000',
            'color': '#fff',
            'padding': '12px 24px',
            'border': 'none',
            'font-size': '16px',
            'margin-right': '10px',
            'font-family': font_family,
            'cursor': 'pointer'
        }),
        html.Button('Stop Recording', id='max-force-stop-button', n_clicks=0, style={
            'background-color': '#555',
            'color': '#fff',
            'padding': '12px 24px',
            'border': 'none',
            'font-size': '16px',
            'margin-right': '10px',
            'font-family': font_family,
            'cursor': 'pointer'
        }),
        html.Button('Save Data to CSV', id='save-button', n_clicks=0, style={
            'background-color': '#888',
            'color': '#fff',
            'padding': '12px 24px',
            'border': 'none',
            'font-size': '16px',
            'font-family': font_family,
            'cursor': 'pointer'
        })
    ], style={
        'textAlign': 'center',
        'margin-top': '30px',
        'font-family': font_family
    }),

    # Confirmation message for saving data
    html.Div(id='save-confirmation', style={
        'margin-top': '20px',
        'color': '#000',
        'font-size': '16px',
        'textAlign': 'center',
        'padding': '10px',
        'background-color': '#f8f8f8',
        'border-radius': '8px',
        'width': '60%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'font-family': font_family
    })
], style={'font-family': font_family})
