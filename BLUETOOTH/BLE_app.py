from dash import dcc, html, Dash, Input, Output
from BLE_layouts import BLE_max_force, BLE_calibration, BLE_arcade, BLE_home
from BLE_callbacks import BLE_max_force_callbacks, BLE_navigation_callbacks, BLE_arcade_callbacks, BLE_calibration_callbacks  # Use the new BLE calibration callbacks
import os

app = Dash(__name__)

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
    html.Div(id='page-content')
])

# Callback to render the correct page layout
@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/max-force-test':
        return BLE_max_force.layout
    elif pathname == '/calibration':
        return BLE_calibration.layout
    elif pathname == '/arcade':
        return BLE_arcade.layout
    return BLE_home.layout  # Default to the home page

# Register callbacks
BLE_max_force_callbacks.register_callbacks(app)
BLE_navigation_callbacks.register_callbacks(app)
BLE_arcade_callbacks.register_callbacks(app)
BLE_calibration_callbacks.register_callbacks(app)  # Register BLE callbacks

if __name__ == '__main__':
    app.run_server(debug=True)
