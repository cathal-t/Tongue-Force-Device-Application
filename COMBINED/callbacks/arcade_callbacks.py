from dash import Input, Output
import subprocess
import os
from utils.communication_utils import comm_handler  # Import the global communication handler

def register_callbacks(app):
    # Pong button click event to launch pong.py
    @app.callback(
        Output('pong-button', 'n_clicks'),  # No real output, we just reset clicks
        [Input('pong-button', 'n_clicks')]
    )
    def launch_pong(n_clicks):
        if n_clicks > 0:
            # Launch the correct pong.py based on the selected communication mode
            if comm_handler.mode == 'BLE':
                pong_script = os.path.join('BLE_pong.py')  # BLE version
            else:
                pong_script = os.path.join('Serial_pong.py')  # Serial version
            subprocess.Popen(['python', pong_script])
        return 0  # Reset the button clicks after launching the game

    # Flappy Bird button click event to launch flappy.py
    @app.callback(
        Output('flappy-bird-button', 'n_clicks'),  # No real output, we just reset clicks
        [Input('flappy-bird-button', 'n_clicks')]
    )
    def launch_flappy(n_clicks):
        if n_clicks > 0:
            # Launch the correct flappy.py based on the selected communication mode
            if comm_handler.mode == 'BLE':
                flappy_script_path = os.path.join('BLE_FlappyBird', 'BLE_flappy.py')  # BLE version
            else:
                flappy_script_path = os.path.join('Serial_FlappyBird', 'Serial_flappy.py')  # Serial version
            subprocess.Popen(['python', flappy_script_path])
        return 0  # Reset the button clicks after launching the game

    # Placeholder for the other button
    @app.callback(
        Output('other-button', 'n_clicks'),
        [Input('other-button', 'n_clicks')]
    )
    def launch_other(n_clicks):
        # Logic for launching other scripts or actions can be added here
        return 0
