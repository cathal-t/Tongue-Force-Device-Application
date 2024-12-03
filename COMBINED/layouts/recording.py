# layouts/recording.py

from dash import html, dcc
import dash_bootstrap_components as dbc

# Common styles
font_family = 'Helvetica, Arial, sans-serif'
box_style = {
    'flex': '1',
    'textAlign': 'left',
    'padding': '20px',
    'backgroundColor': '#f8f8f8',
    'border-radius': '8px',
    'margin': '0 10px',
    'display': 'flex',
    'flexDirection': 'column',
    'font-family': font_family
}
heading_style = {
    'color': '#000',
    'margin-bottom': '5px',
    'font-family': font_family,
    'font-size': '20px',
    'font-weight': 'bold'
}
label_style = {
    'font-family': font_family,
    'font-size': '16px',
    'margin-top': '10px'
}
dropdown_style = {
    'margin-bottom': '20px',
    'font-family': font_family
}
button_style = {
    'margin-bottom': '10px',
    'font-family': font_family,
    'width': '100%',
    'padding': '12px',
    'backgroundColor': '#5783db',
    'font-size': '28px',
    'border-radius': '8px'
}

layout = html.Div([
    html.H1('Live Sensor Data Recording', style={
        'textAlign': 'center',
        'color': '#000',
        'margin-bottom': '20px',
        'margin-top': '20px',
        'font-family': font_family
    }),

    # Connection Status
    html.Div(id='recording-connection-status', style={
        'color': '#000',
        'font-size': '20px',
        'textAlign': 'center',
        'margin-bottom': '10px',
        'font-family': font_family
    }),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                # Sidebar content
                html.Div([
                    html.H2("Select Patient and Session", style={'textAlign': 'center', 'font-family': font_family}),
                    html.Hr(),
                    html.Label('Select Patient ID', style=label_style),
                    dcc.Dropdown(
                        id='recording-patient-id-dropdown',
                        options=[],  # Options will be populated dynamically
                        placeholder='Search or select a patient ID',
                        style=dropdown_style
                    ),
                    html.Label('Select Statistics File(s)', style=label_style),
                    dcc.Checklist(
                        id='recording-session-checklist',
                        options=[],  # Options will be populated based on selected patient
                        value=[],
                        style={
                            'margin-bottom': '20px',
                            'font-family': font_family
                        }
                    ),
                    # Existing file warning div for live updates
                    html.Div(id='recording-file-warning', style={
                        'color': 'red',
                        'margin-top': '16px',
                        'font-size': '20px',
                        'font-family': font_family
                    }),
                    html.Button('Start', id='recording-start-button', n_clicks=0,
                                style={
                                    'background-color': '#28a745',  # Green color
                                    'color': '#fff',
                                    'padding': '16px 32px',
                                    'border': 'none',
                                    'font-size': '32px',
                                    'border-radius': '12px',
                                    'margin-bottom': '20px',
                                    'font-family': font_family,
                                    'cursor': 'pointer',
                                    'width': '100%'
                                }),
                    html.Button('Stop', id='recording-stop-button', n_clicks=0,
                                style={
                                    'background-color': '#dc3545',  # Red color
                                    'color': '#fff',
                                    'padding': '16px 32px',
                                    'border': 'none',
                                    'font-size': '32px',
                                    'border-radius': '12px',
                                    'font-family': font_family,
                                    'cursor': 'pointer',
                                    'width': '100%'
                                }),
                    # Confirmation message for saving data
                    html.Div(id='recording-save-confirmation', style={
                        'margin-top': '20px',
                        'color': '#008000',
                        'font-size': '22px',
                        'textAlign': 'center',
                        'padding': '10px',
                        'background-color': '#f8f8f8',
                        'border-radius': '18px',
                        'font-family': font_family
                    }),
                    # Warnings
                    html.Div(id='recording-id-warning', style={
                        'color': 'red',
                        'margin-top': '16px',
                        'font-size': '20px',
                        'font-family': font_family
                    }),
                    html.Div(id='recording-file-warning-start', style={
                        'color': 'red',
                        'textAlign': 'center',
                        'margin-top': '16px',
                        'font-size': '20px',
                        'font-family': font_family
                    }),
                ], style=box_style),
            ], width=3, style={
                #'border-right': '1px solid #ddd',
                'padding': '20px',
                'backgroundColor': '#f8f8f8'
            }),

            dbc.Col([
                # Main content
                html.Div(
                    dcc.Graph(
                        id='recording-live-graph',
                        config={'displayModeBar': False},
                        style={
                            'margin-bottom': '20px',
                            'border-radius': '8px',
                            'height': '1000px'  # Increased height
                        }
                    ),
                    style={
                        'width': '100%',
                        'margin-left': 'auto',
                        'margin-right': 'auto',
                    }
                ),
                # Live data display (Current Sensor Value, Max Sensor Value)
                html.Div([
                    html.Div([
                        html.H3('Current Sensor Value:', style=heading_style),
                        html.H4(id='recording-live-sensor-value', style={
                            'font-size': '24px',
                            'font-weight': 'bold',
                            'color': '#000',
                            'margin': '5px 0',
                            'font-family': font_family
                        }),
                    ], style=box_style),

                    html.Div([
                        html.H3('Maximum Sensor Value:', style=heading_style),
                        html.H4(id='recording-max-sensor-value', style={
                            'font-size': '24px',
                            'font-weight': 'bold',
                            'color': '#000',
                            'margin': '5px 0',
                            'font-family': font_family
                        }),
                    ], style=box_style),
                ], style={
                    'display': 'flex',
                    'justify-content': 'space-around',
                    'align-items': 'stretch',
                    'margin-bottom': '40px',
                    'width': '100%',
                    'margin-left': 'auto',
                    'margin-right': 'auto',
                }),
            ], width=9, style={'padding': '20px'}),
        ])
    ], fluid=True),

    # Interval for real-time updates
    dcc.Interval(id='recording-graph-update', interval=100, n_intervals=0),
    dcc.Interval(id='recording-connection-interval', interval=100, n_intervals=0),

    # Store to keep track of unsaved data
    dcc.Store(id='recording-unsaved-data-flag', data=False),

    dbc.Modal(
        [
            dbc.ModalHeader("Save Data", style={'font-family': font_family}),
            dbc.ModalBody("Do you want to save the recorded data?", style={'font-family': font_family}),
            dbc.ModalFooter(
                dbc.Row(
                    [
                        dbc.Col(
                            dbc.Button("SAVE", id="recording-modal-save-button", color="danger", style={'text-transform': 'uppercase', 'font-family': font_family}),
                            width="auto"
                        ),
                        dbc.Col(
                            dbc.Button("Don't Save", id="recording-modal-dont-save-button", color="secondary", style={'font-family': font_family}),
                            width="auto",
                            className="ml-auto"
                        ),
                    ],
                    align="center",
                    className="w-100 d-flex justify-content-between"
                )
            ),
        ],
        id="recording-save-data-modal",
        is_open=False,
        centered=True,
    ),

    # Dummy output to prevent callback errors (if needed)
    html.Div(id='recording-dummy-output', style={'display': 'none'}),

], style={
    'font-family': font_family,
    'backgroundColor': '#f8f8f8'
})
