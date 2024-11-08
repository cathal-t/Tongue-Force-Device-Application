from dash import dcc, html
import dash_bootstrap_components as dbc  # Import dash-bootstrap-components

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
        'margin-bottom': '20px',
        'margin-top': '20px',
        'font-family': font_family
    }),

    # Connection Status
    html.Div(id='connection-status', style={
        'color': '#000',
        'font-size': '20px',
        'textAlign': 'center',
        'margin-bottom': '10px',
        'font-family': font_family
    }),

    # Patient ID input
    html.Div([
        dcc.Input(
            id='patient-id',
            type='text',
            placeholder='Enter Patient ID',
            style={
                'width': '100%',
                'padding': '12px',
                'font-size': '20px',
                'border': '1px solid #ccc',
                'border-radius': '2px',
                'background-color': '#fff',
                'font-family': font_family
            }
        ),
        html.Div(id='id-warning', style={
            'color': 'red',
            'margin-top': '16px',
            'font-size': '20px',
            'font-family': font_family
        })
    ], style={
        'margin-bottom': '10px',
        'padding': '20px',
        'border-radius': '8px',
        'background-color': '#f8f8f8',
        'width': '60%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'font-family': font_family
    }),

    # Graph display for live data
    html.Div(
        dcc.Graph(id='live-graph', config={'displayModeBar': False}, style={
            'margin-bottom': '20px',
            'border-radius': '8px',
            'height': '500px'
        }),
        style={
            'width': '85%',
            'margin-left': 'auto',
            'margin-right': 'auto',
        }
    ),

    # Buttons to start/stop recording (removed the Save Data button)
    html.Div([
        html.Div([
            html.Button('Start', id='max-force-start-button', n_clicks=0, style={
                'background-color': '#28a745',  # Green color
                'color': '#fff',
                'padding': '16px 32px',
                'border': 'none',
                'font-size': '32px',
                'border-radius': '12px',
                'margin-right': '300px',
                'font-family': font_family,
                'cursor': 'pointer'
            }),
            html.Button('Stop', id='max-force-stop-button', n_clicks=0, style={
                'background-color': '#dc3545',  # Red color
                'color': '#fff',
                'padding': '16px 32px',
                'border': 'none',
                'font-size': '32px',
                'border-radius': '12px',
                'font-family': font_family,
                'cursor': 'pointer'
            })
        ], style={'margin-bottom': '20px'}),
    ], style={
        'textAlign': 'center',
        'margin-bottom': '20px',
        'font-family': font_family
    }),

    # Confirmation message for saving data
    html.Div(id='save-confirmation', style={
        'margin-top': '20px',
        'color': '#008000',
        'font-size': '22px',
        'textAlign': 'center',
        'padding': '10px',
        'background-color': '#f8f8f8',
        'border-radius': '18px',
        'width': '60%',
        'margin-left': 'auto',
        'margin-right': 'auto',
        'margin-bottom': '20px',
        'font-family': font_family
    }),

    # Live data display (Current Sensor Value, Max Sensor Value, Percentages)
    html.Div([
        html.Div([
            html.H3('Current Sensor Value:', style=heading_style),
            html.H4(id='live-sensor-value', style=value_style),
        ], style=box_style),

        html.Div([
            html.H3('Maximum Sensor Value:', style=heading_style),
            html.H4(id='max-sensor-value', style=value_style),
        ], style=box_style),

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

    # Interval for real-time updates
    dcc.Interval(id='graph-update', interval=100, n_intervals=0),

    # Store to keep track of unsaved data
    dcc.Store(id='unsaved-data-flag', data=False),

    dbc.Modal(
        [
            dbc.ModalHeader("Save Data", style={'font-family': font_family}),
            dbc.ModalBody("Do you want to save the recorded data?", style={'font-family': font_family}),
            dbc.ModalFooter(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button("SAVE", id="modal-save-button", color="danger", style={'text-transform': 'uppercase', 'font-family': font_family}),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button("Don't Save", id="modal-dont-save-button", color="secondary", style={'font-family': font_family}),
                            width="auto",
                            className="ml-auto"  # Moves the "Don't Save" button to the far right
                        ),
                    ],
                    align="center",  # Aligns buttons vertically in the center
                    className="w-100 d-flex justify-content-between"  # Spreads buttons across the modal footer
                )
            ),
        ],
        id="save-data-modal",
        is_open=False,
        centered=True,  # Centers the modal on the screen
    ),

], style={
    'font-family': font_family,
    'zoom': '0.9'  # Set the zoom level to 90%
})
