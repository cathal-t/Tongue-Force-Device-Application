from dash import dcc, html, Dash, Input, Output
from layouts import max_force, calibration, arcade, home, data_analysis  # Import data_analysis layout
from callbacks import (
    max_force_callbacks,
    navigation_callbacks,
    arcade_callbacks,
    calibration_callbacks,
    data_analysis_callbacks  # Import data_analysis_callbacks
)
from utils.communication_utils import comm_handler
import os
import dash_bootstrap_components as dbc
import webbrowser
from threading import Timer

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Function to open the default web browser
def open_browser():
    webbrowser.open_new("http://127.0.0.1:8050")

def load_calibration_data():
    try:
        filename = os.path.join(os.path.dirname(__file__), 'calibration_data.txt')
        with open(filename, 'r') as f:
            data = f.read().strip()
            if data:
                calibration_slope, calibration_intercept = map(float, data.split(','))
                return {'slope': calibration_slope, 'intercept': calibration_intercept}
    except (FileNotFoundError, ValueError):
        pass
    return {}

# Define the main layout with dcc.Location to handle page navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),

    # Shared Store for calibration coefficients
    dcc.Store(id='shared-calibration-coefficients', data=load_calibration_data()),

    # Page content dynamically updated by URL
    html.Div(id='page-content')
])

# Callback to render the correct page layout
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/max-force-test':
        return max_force.layout  # Use shared max_force layout
    elif pathname == '/calibration':
        return calibration.layout  # Use shared calibration layout
    elif pathname == '/arcade':
        return arcade.layout  # Use shared arcade layout
    elif pathname == '/data-analysis':  # Add this condition
        return data_analysis.layout  # Return the data_analysis layout
    return home.layout  # Default to the home page

# Register callbacks
max_force_callbacks.register_callbacks(app)
navigation_callbacks.register_callbacks(app)
arcade_callbacks.register_callbacks(app)
calibration_callbacks.register_callbacks(app)
data_analysis_callbacks.register_callbacks(app)  # Register data analysis callbacks

if __name__ == '__main__':
    if 'WERKZEUG_RUN_MAIN' not in os.environ:  # Prevent opening browser twice
        Timer(1, open_browser).start()
    app.run_server(debug=True)
