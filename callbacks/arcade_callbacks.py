from dash import Input, Output
import subprocess
import os

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

    # Flappy Bird button click event to launch flappy.py
    @app.callback(
        Output('flappy-bird-button', 'n_clicks'),  # No real output, we just reset clicks
        [Input('flappy-bird-button', 'n_clicks')]
    )
    def launch_flappy(n_clicks):
        if n_clicks > 0:
            # Launch flappy.py from the FlappyBird folder
            flappy_script_path = os.path.join('FlappyBird', 'flappy.py')
            subprocess.Popen(['python', flappy_script_path])  # Make sure the path is correct
        return 0  # Reset the button clicks after launching the game

    # Placeholder for the other button
    @app.callback(
        Output('other-button', 'n_clicks'),
        [Input('other-button', 'n_clicks')]
    )
    def launch_other(n_clicks):
        # You can add logic for launching other scripts or actions here
        return 0
