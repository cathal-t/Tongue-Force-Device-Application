from dash import Input, Output
import subprocess

def register_callbacks(app):
    # Pong button click event to launch pong.py
    @app.callback(
        Output('pong-button', 'n_clicks'),  # No real output, we just reset clicks
        [Input('pong-button', 'n_clicks')]
    )
    def launch_pong(n_clicks):
        if n_clicks > 0:
            # Launch pong.py
            subprocess.Popen(['python', 'pong.py'])  # Replace with actual path to pong.py
        return 0  # Reset the button clicks after launching the game

    # Placeholder for future Flappy Bird and Other buttons
    @app.callback(
        [Output('flappy-bird-button', 'n_clicks'),
         Output('other-button', 'n_clicks')],
        [Input('flappy-bird-button', 'n_clicks'),
         Input('other-button', 'n_clicks')]
    )
    def placeholders_for_future(n_clicks_flappy, n_clicks_other):
        # Do nothing for now; placeholder for future games
        return 0, 0
