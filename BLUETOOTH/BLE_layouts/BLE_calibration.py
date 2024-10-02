from dash import html, dcc

layout = html.Div([
    # Title of the Calibration Page
    html.H2("Calibration Page", style={
        'textAlign': 'center',
        'margin-bottom': '20px',
        'color': '#333',
        'font-family': 'Arial, sans-serif'
    }),
    
    # Add the BLE Connectivity Status Display
    html.Div(id='ble-connection-status_calibration', style={
        'color': '#007BFF',
        'font-size': '18px',
        'textAlign': 'center',
        'margin-bottom': '20px'
    }),

    # Start and Stop Recording Buttons
    html.Div([
        html.Button("Start Recording", id="calibration-start-button", n_clicks=0, style={
            'background-color': '#007BFF',
            'color': '#fff',
            'padding': '10px 20px',
            'border': 'none',
            'border-radius': '4px',
            'font-size': '16px',
            'margin-right': '10px',
            'cursor': 'pointer'
        }),
        html.Button("Stop Recording", id="calibration-stop-button", n_clicks=0, style={
            'background-color': '#dc3545',
            'color': '#fff',
            'padding': '10px 20px',
            'border': 'none',
            'border-radius': '4px',
            'font-size': '16px',
            'cursor': 'pointer'
        }),
    ], style={'textAlign': 'center', 'margin-bottom': '20px'}),

    # Section for live sensor value display
    html.Div([
        html.H4("Live Sensor Value:", style={
            'textAlign': 'center',
            'color': '#333',
            'font-family': 'Arial, sans-serif'
        }),
        html.Div(id='live-sensor-value-calibration', children="N/A", style={
            'textAlign': 'center',
            'font-size': '36px',
            'font-weight': 'bold',
            'color': '#28a745',
            'margin-bottom': '20px',
            'font-family': 'Arial, sans-serif'
        }),
    ], style={
        'background-color': '#f8f9fa',
        'padding': '20px',
        'border-radius': '8px',
        'margin-bottom': '20px'
    }),

    # Interval component for live updates
    dcc.Interval(id='live-update-interval', interval=500, n_intervals=0),

    # Section for input fields (Applied Weight and Sensor Values)
    html.Div([
        html.H4("Enter Calibration Data:", style={
            'margin-bottom': '20px',
            'textAlign': 'center',
            'color': '#333',
            'font-family': 'Arial, sans-serif'
        }),
        html.Div([
            dcc.Input(
                id='applied-weight-input',
                type='number',
                placeholder='Applied Weight (Newtons)',
                step=0.1,
                style={
                    'margin-right': '10px',
                    'padding': '10px',
                    'width': '250px',
                    'font-size': '16px',
                    'border': '1px solid #ced4da',
                    'border-radius': '4px',
                    'margin-bottom': '10px'
                }
            ),
            dcc.Input(
                id='sensor-value-input',
                type='number',
                placeholder='Sensor Value (optional)',
                step=1,
                style={
                    'margin-right': '10px',
                    'padding': '10px',
                    'width': '250px',
                    'font-size': '16px',
                    'border': '1px solid #ced4da',
                    'border-radius': '4px',
                    'margin-bottom': '10px'
                }
            ),
            html.Button('Add Data', id='add-calibration-data-btn', n_clicks=0, style={
                'background-color': '#28a745',
                'color': '#fff',
                'padding': '10px 20px',
                'border': 'none',
                'border-radius': '4px',
                'font-size': '16px',
                'cursor': 'pointer',
                'margin-bottom': '10px'
            }),
        ], style={'textAlign': 'center'}),
    ], style={'margin-bottom': '40px'}),

    # Display the table of entered values
    html.Div([
        html.H4("Calibration Data:", style={
            'textAlign': 'center',
            'margin-bottom': '20px',
            'color': '#333',
            'font-family': 'Arial, sans-serif'
        }),
        html.Div(id='calibration-data-table', style={
            'textAlign': 'center',
            'font-family': 'Arial, sans-serif'
        }),
    ], style={'margin-bottom': '40px'}),

    # Buttons to trigger the line of best fit calculation and reset calibration data
    html.Div([
        html.Button('Calculate Line of Best Fit', id='calculate-fit-btn', n_clicks=0, style={
            'background-color': '#17a2b8',
            'color': '#fff',
            'padding': '10px 30px',
            'border': 'none',
            'border-radius': '4px',
            'font-size': '18px',
            'cursor': 'pointer',
            'margin-right': '10px'
        }),
        html.Button('Reset Calibration Data', id='reset-calibration-btn', n_clicks=0, style={
            'background-color': '#6c757d',
            'color': '#fff',
            'padding': '10px 30px',
            'border': 'none',
            'border-radius': '4px',
            'font-size': '18px',
            'cursor': 'pointer'
        }),
    ], style={'textAlign': 'center', 'margin-bottom': '20px'}),

    # Display the calculated slope and intercept (line of best fit)
    html.Div(id='calibration-result', style={
        'textAlign': 'center',
        'font-size': '20px',
        'margin-top': '20px',
        'color': '#333',
        'font-family': 'Arial, sans-serif'
    }),

    # Button to save the calibration data
    html.Div([
        html.Button("Save Calibration", id='save-calibration-btn', n_clicks=0, style={
            'background-color': '#ffc107',
            'color': '#fff',
            'padding': '10px 30px',
            'border': 'none',
            'border-radius': '4px',
            'font-size': '18px',
            'cursor': 'pointer'
        }),
    ], style={'textAlign': 'center', 'margin-top': '40px'}),

    html.Div(id='calibration-save-confirmation', style={
        'textAlign': 'center',
        'font-size': '18px',
        'margin-top': '20px',
        'color': '#007BFF',
        'font-family': 'Arial, sans-serif'
    }),

    # Store components to hold calibration data and coefficients
    dcc.Store(id='calibration-data-store', data=[]),
    dcc.Store(id='calibration-coefficients-store', data={})
], style={
    'max-width': '800px',
    'margin': '0 auto',
    'padding': '20px',
    'font-family': 'Arial, sans-serif',
    'background-color': '#ffffff'
})
