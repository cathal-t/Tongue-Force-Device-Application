from dash import html, dcc

layout = html.Div([

    # Title of the Calibration Page
    html.H2("Calibration Page"),

    # Start Recording Button (to initiate live sensor data collection)
    html.Button("Start Recording", id="start-button", n_clicks=0),

    # Section for live sensor value display
    html.Div([
        html.H4("Live Sensor Value:"),
        html.Div(id='live-sensor-value-calibration', children="N/A"),  # This will be updated live
    ]),

    # Section for input table (Applied Weight and Sensor Values)
    html.Div([
        html.H4("Enter Calibration Data:"),
        dcc.Input(
            id='applied-weight-input', 
            type='number', 
            placeholder='Applied Weight (Newtons)', 
            step=0.1
        ),
        dcc.Input(
            id='sensor-value-input', 
            type='number', 
            placeholder='Sensor Value (optional)', 
            step=1
        ),  # Optional if live value is used
        html.Button('Add Data', id='add-calibration-data-btn', n_clicks=0),
    ]),
    
    # Display the table of entered values
    html.Div([
        html.H4("Calibration Data:"),
        html.Table(id='calibration-data-table')  # This table will be dynamically updated
    ]),

    # Button to trigger the line of best fit calculation
    html.Button('Calculate Line of Best Fit', id='calculate-fit-btn', n_clicks=0),
    
    # Display the calculated slope and intercept (line of best fit)
    html.Div(id='calibration-result'),

    # Button to save the calibration data
    html.Button("Save Calibration", id='save-calibration-btn', n_clicks=0),
    html.Div(id='calibration-save-confirmation')
])
