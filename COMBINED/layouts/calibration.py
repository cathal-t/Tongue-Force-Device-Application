import dash_bootstrap_components as dbc
from dash import html, dcc

layout = dbc.Container([
    # Title of the Calibration Page
    dbc.Row(
        dbc.Col(
            html.H2("Calibration Page", className="text-center mb-4 text-primary")
        )
    ),

    # Connection Status Display as an Alert with light background
    dbc.Row(
        dbc.Col(
            dbc.Alert(
                id='connection-status_calibration',  # Updated ID
                color='light',
                className="text-center mb-6",
                style={'color': '#007BFF'}  
            ),
            width=12
        )
    ),


    # Start and Stop Recording Buttons centered
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    "Start Recording",
                    id="calibration-start-button",
                    color="primary",
                    n_clicks=0
                ),
                width="auto"
            ),
            dbc.Col(
                dbc.Button(
                    "Stop Recording",
                    id="calibration-stop-button",
                    color="danger",
                    n_clicks=0
                ),
                width="auto"
            ),
        ],
        justify="center",
        className="mb-4"
    ),

    # Section for live sensor value display in a Card
    dbc.Row(
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H5(
                        "Live Sensor Value:",
                        className="text-center",
                        style={'color': '#333', 'font-weight': 'bold', 'font-family': 'Arial, sans-serif'}
                    ),
                    html.H1(
                        id='live-sensor-value-calibration',
                        children="N/A",
                        className="text-success display-6 text-center",
                        style={
                            'font-size': '30px',
                            'font-weight': 'bold',
                            'margin-bottom': '10px',
                            'font-family': 'Arial, sans-serif'
                        }
                    )
                ]),
                className="shadow-sm mb-4",
                style={
                    'background-color': '#f8f9fa',
                    'padding': '10px',
                    'border-radius': '8px'
                }
            ),
            width=8
        ),
        justify="center"
    ),

    # Interval component for live updates
    dcc.Interval(id='live-update-interval', interval=500, n_intervals=0),

    # Section for input fields in a Card
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5(
                        "Enter Calibration Data",
                        className="text-center text-secondary",
                        style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}
                    )
                ),
                dbc.CardBody(
                    dbc.Form([
                        dbc.Row([
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Applied Weight (Newtons)",
                                        html_for='applied-weight-input',
                                        className="text-center",
                                        style={'font-family': 'Arial, sans-serif'}
                                    ),
                                    dbc.Input(
                                        id='applied-weight-input',
                                        type='number',
                                        placeholder='Applied Weight (Newtons)',
                                        step=0.1,
                                        style={
                                            'padding': '10px',
                                            'width': '100%',
                                            'font-size': '16px',
                                            'border': '1px solid #ced4da',
                                            'border-radius': '4px',
                                            'margin-bottom': '10px'
                                        }
                                    ),
                                ],
                                width=4,
                                className="mx-auto"
                            ),
                            dbc.Col(
                                [
                                    dbc.Label(
                                        "Sensor Value (optional)",
                                        html_for='sensor-value-input',
                                        className="text-center",
                                        style={'font-family': 'Arial, sans-serif'}
                                    ),
                                    dbc.Input(
                                        id='sensor-value-input',
                                        type='number',
                                        placeholder='Sensor Value (optional)',
                                        step=1,
                                        style={
                                            'padding': '10px',
                                            'width': '100%',
                                            'font-size': '16px',
                                            'border': '1px solid #ced4da',
                                            'border-radius': '4px',
                                            'margin-bottom': '10px'
                                        }
                                    ),
                                ],
                                width=4,
                                className="mx-auto"
                            )
                        ], justify="center"),
                        dbc.Row(
                            dbc.Col(
                                dbc.Button(
                                    'Add Data',
                                    id='add-calibration-data-btn',
                                    n_clicks=0,
                                    color="success",
                                    className="mt-3 w-100",
                                    style={
                                        'padding': '10px 20px',
                                        'font-size': '16px',
                                        'border-radius': '4px',
                                        'cursor': 'pointer',
                                        'margin-bottom': '10px'
                                    }
                                ),
                                width=5,
                                className="mx-auto"
                            ),
                            justify="center"
                        )
                    ])
                )
            ], className="mb-4"),
            width=8
        ),
        justify="center"
    ),

    # Display the table of entered values
    dbc.Row(
        dbc.Col(
            dbc.Card([
                dbc.CardHeader(
                    html.H5(
                        "Calibration Data",
                        className="text-center text-secondary",
                        style={'font-family': 'Arial, sans-serif', 'font-weight': 'bold'}
                    )
                ),
                dbc.CardBody(
                    dbc.Table(
                        id='calibration-data-table',
                        bordered=True,
                        hover=True,
                        responsive=True,
                        striped=True,
                        style={'textAlign': 'center', 'font-family': 'Arial, sans-serif'}
                    )
                )
            ], className="mb-4"),
            width=8
        ),
        justify="center"
    ),

    # Buttons to trigger calculation and reset calibration data centered
    dbc.Row(
        [
            dbc.Col(
                dbc.Button(
                    'Calculate Line of Best Fit',
                    id='calculate-fit-btn',
                    n_clicks=0,
                    color="info",
                    style={
                        'padding': '10px 30px',
                        'font-size': '18px',
                        'border-radius': '4px',
                        'margin-right': '10px',
                        'cursor': 'pointer'
                    }
                ),
                width="auto"
            ),
            dbc.Col(
                dbc.Button(
                    'Reset Calibration Data',
                    id='reset-calibration-btn',
                    n_clicks=0,
                    color="secondary",
                    style={
                        'padding': '10px 30px',
                        'font-size': '18px',
                        'border-radius': '4px',
                        'cursor': 'pointer'
                    }
                ),
                width="auto"
            ),
        ],
        justify="center",
        className="mb-4"
    ),

    # Display the calculated slope and intercept (line of best fit)
    dbc.Row(
        dbc.Col(
            dbc.Alert(
                id='calibration-result',
                color='light',
                className="text-center mb-4",
                style={
                    'font-size': '20px',
                    'color': '#333',
                    'font-family': 'Arial, sans-serif'
                }
            ),
            width=8
        ),
        justify="center"
    ),

    # Button to save the calibration data centered
    dbc.Row(
        dbc.Col(
            dbc.Button(
                "Save Calibration",
                id='save-calibration-btn',
                n_clicks=0,
                color="warning",
                style={
                    'padding': '10px 30px',
                    'font-size': '18px',
                    'border-radius': '4px',
                    'cursor': 'pointer'
                }
            ),
            width="auto"
        ),
        justify="center",
        className="mb-4"
    ),

    # Confirmation message for saving calibration
    dbc.Row(
        dbc.Col(
            dbc.Alert(
                id='calibration-save-confirmation',
                color='light',
                className="text-center mb-4",
                style={
                    'font-size': '18px',
                    'color': '#333',
                    'font-family': 'Arial, sans-serif'
                }
            ),
            width=8
        ),
        justify="center"
    ),

    # Store components to hold calibration data and coefficients
    dcc.Store(id='calibration-data-store', data=[]),
    dcc.Store(id='calibration-coefficients-store', data={})
], fluid=True, className="p-4 bg-light")
