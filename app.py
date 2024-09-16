from dash import dcc, html, Dash, Input, Output
from layouts import max_force, calibration, arcade, home
from callbacks import max_force_callbacks, navigation_callbacks, arcade_callbacks, calibration_callbacks  # Import callbacks

import os

# Ensure the 'profiles' directory exists
if not os.path.exists('profiles'):
    os.makedirs('profiles')


app = Dash(__name__)

# Define the main layout with dcc.Location to handle page navigation
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
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
