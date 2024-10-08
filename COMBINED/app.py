from dash import dcc, html, Dash, Input, Output
from layouts import max_force, calibration, arcade, home  # Updated to use shared layouts
from callbacks import max_force_callbacks, navigation_callbacks, arcade_callbacks, calibration_callbacks
from utils.communication_utils import comm_handler  # Import the communication handler
import os
import dash_bootstrap_components as dbc

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

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
        return max_force.layout  # Use shared max_force layout (not BLE-specific)
    elif pathname == '/calibration':
        return calibration.layout  # Use shared calibration layout
    elif pathname == '/arcade':
        return arcade.layout  # Use shared arcade layout
    return home.layout  # Default to the home page

# Register callbacks for both Serial and BLE
max_force_callbacks.register_callbacks(app)  # Shared callback for force test
navigation_callbacks.register_callbacks(app)  # Handles navigation and communication mode
arcade_callbacks.register_callbacks(app)  # Shared callback for arcade games
calibration_callbacks.register_callbacks(app)  # Shared callback for calibration

if __name__ == '__main__':
    app.run_server(debug=True)
