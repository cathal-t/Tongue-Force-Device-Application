from dash import dcc, html, Dash, Input, Output
from layouts import max_force, calibration, arcade, home
from callbacks import max_force_callbacks, navigation_callbacks, arcade_callbacks, calibration_callbacks  # Import callbacks
import os

# Import additional modules
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
        return max_force.layout
    elif pathname == '/calibration':
        return calibration.layout
    elif pathname == '/arcade':
        return arcade.layout
    return home.layout  # Default to the home page

# Register callbacks
max_force_callbacks.register_callbacks(app)
navigation_callbacks.register_callbacks(app)
arcade_callbacks.register_callbacks(app)
calibration_callbacks.register_callbacks(app)

if __name__ == '__main__':
    app.run_server(debug=True)
