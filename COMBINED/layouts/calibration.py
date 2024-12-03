# layouts/calibration.py

from dash import html, dcc
import dash_bootstrap_components as dbc

# Common styles
font_family = 'Helvetica, Arial, sans-serif'
heading_style = {
    'color': '#000',
    'font-family': font_family,
    'margin-bottom': '10px',
    'font-weight': 'bold',
    'text-align': 'center'
}
label_style = {
    'font-family': font_family,
    'font-size': '16px',
    'margin-top': '10px',
    'margin-bottom': '5px'
}
input_style = {
    'padding': '10px',
    'width': '100%',
    'font-size': '16px',
    'border': '1px solid #ced4da',
    'border-radius': '4px',
    'margin-bottom': '10px',
    'font-family': font_family
}
button_style = {
    'padding': '12px 24px',
    'font-size': '18px',
    'border-radius': '8px',
    'font-family': font_family,
    'cursor': 'pointer',
    'margin': '10px'
}
card_style = {
    'background-color': '#f8f8f8',
    'padding': '20px',
    'border-radius': '8px',
    'margin-bottom': '20px',
    'font-family': font_family
}
alert_style = {
    'font-size': '18px',
    'color': '#333',
    'font-family': font_family,
    'text-align': 'center',
    'margin-bottom': '20px'
}

layout = html.Div([
    html.H1('Calibration Page', style={
        'textAlign': 'center',
        'color': '#000',
        'margin-top': '20px',
        'margin-bottom': '20px',
        'font-family': font_family
    }),

    # Connection Status
    html.Div(id='connection-status_calibration', style={
        'color': '#000',
        'font-size': '20px',
        'textAlign': 'center',
        'margin-bottom': '20px',
        'font-family': font_family
    }),

    # Start and Stop Recording Buttons
    html.Div([
        html.Button('Start Recording', id='calibration-start-button', n_clicks=0, style={
            **button_style,
            'background-color': '#28a745',  # Green
            'color': '#fff',
        }),
        html.Button('Stop Recording', id='calibration-stop-button', n_clicks=0, style={
            **button_style,
            'background-color': '#dc3545',  # Red
            'color': '#fff',
        }),
    ], style={
        'textAlign': 'center',
        'margin-bottom': '20px',
    }),

    # Live Sensor Value Display
    html.Div([
        html.H3('Live Sensor Value:', style=heading_style),
        html.H1(id='live-sensor-value-calibration', children="N/A", style={
            'font-size': '40px',
            'font-weight': 'bold',
            'color': '#000',
            'margin-bottom': '20px',
            'font-family': font_family,
            'text-align': 'center'
        }),
    ], style={
        'width': '60%',
        'margin': '0 auto',
        'background-color': '#f8f8f8',
        'padding': '20px',
        'border-radius': '8px',
        'margin-bottom': '20px',
    }),

    # Interval component for live updates
    dcc.Interval(id='live-update-interval', interval=500, n_intervals=0),

    # Input Fields for Calibration Data
    html.Div([
        html.H3('Enter Calibration Data', style=heading_style),
        html.Div([
            html.Label('Applied Weight (Newtons)', style=label_style),
            dcc.Input(
                id='applied-weight-input',
                type='number',
                placeholder='Applied Weight (Newtons)',
                step=0.1,
                style=input_style
            ),
            html.Label('Sensor Value (optional)', style=label_style),
            dcc.Input(
                id='sensor-value-input',
                type='number',
                placeholder='Sensor Value (optional)',
                step=1,
                style=input_style
            ),
            html.Button('Add Data', id='add-calibration-data-btn', n_clicks=0, style={
                **button_style,
                'background-color': '#007bff',  # Bootstrap primary blue
                'color': '#fff',
                'width': '100%',
                'margin-top': '10px'
            }),
        ], style={
            'width': '100%',
        }),
    ], style={
        'width': '60%',
        'margin': '0 auto',
        **card_style
    }),

    # Calibration Data Table
    html.Div([
        html.H3('Calibration Data', style=heading_style),
        html.Div(id='calibration-data-table', style={
            'textAlign': 'center',
            'font-family': font_family,
            'margin-bottom': '20px'
        }),
    ], style={
        'width': '80%',
        'margin': '0 auto',
        **card_style
    }),

    # Buttons for Calculating Fit and Resetting Data
    html.Div([
        html.Button('Calculate Line of Best Fit', id='calculate-fit-btn', n_clicks=0, style={
            **button_style,
            'background-color': '#17a2b8',  # Info blue
            'color': '#fff',
        }),
        html.Button('Reset Calibration Data', id='reset-calibration-btn', n_clicks=0, style={
            **button_style,
            'background-color': '#6c757d',  # Secondary gray
            'color': '#fff',
        }),
    ], style={
        'textAlign': 'center',
        'margin-bottom': '20px',
    }),

    # Display Calibration Result
    html.Div(id='calibration-result', style={
        **alert_style,
        'background-color': '#e9ecef',
        'padding': '20px',
        'border-radius': '8px',
        'width': '60%',
        'margin': '0 auto',
    }),

    # Save Calibration Button
    html.Div([
        html.Button('Save Calibration', id='save-calibration-btn', n_clicks=0, style={
            **button_style,
            'background-color': '#ffc107',  # Warning yellow
            'color': '#000',
        }),
    ], style={
        'textAlign': 'center',
        'margin-bottom': '20px',
    }),

    # Confirmation Message for Saving Calibration
    html.Div(id='calibration-save-confirmation', style={
        **alert_style,
        'background-color': '#e9ecef',
        'padding': '20px',
        'border-radius': '8px',
        'width': '60%',
        'margin': '0 auto',
    }),

    # Store components to hold calibration data and coefficients
    dcc.Store(id='calibration-data-store', data=[]),
    dcc.Store(id='calibration-coefficients-store', data={})

], style={
    'font-family': font_family,
    'backgroundColor': '#f8f8f8',
    'padding': '20px'
})
