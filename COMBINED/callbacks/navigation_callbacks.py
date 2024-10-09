from dash import Input, Output, callback_context
from utils.communication_utils import comm_handler  # Import the global communication handler

def register_callbacks(app):
    # Callback for page navigation
    @app.callback(
        Output('url', 'pathname'),
        [Input('max-force-button', 'n_clicks'),
         Input('calibration-button', 'n_clicks'),
         Input('arcade-button', 'n_clicks')]
    )
    def navigate_pages(max_force_clicks, calibration_clicks, arcade_clicks):
        # Get the context of which button was clicked
        ctx = callback_context
        if not ctx.triggered:
            return '/'

        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if button_id == 'max-force-button' and max_force_clicks > 0:
            return '/max-force-test'
        elif button_id == 'calibration-button' and calibration_clicks > 0:
            return '/calibration'
        elif button_id == 'arcade-button' and arcade_clicks > 0:
            return '/arcade'

        # Default to home page if no valid button click
        return '/'

    # Callback to update the communication method
    @app.callback(
        Output('comm-method-output', 'children'),  # Update the text below the dropdown
        [Input('comm-method-dropdown', 'value')]   # Listen for changes in the dropdown
    )
    def update_comm_method(selected_method):
        # Validate the selected communication method
        if selected_method in ['Serial', 'BLE']:
            # Only close the current connection if a mode is already active
            if comm_handler.is_connected():
                comm_handler.handler.close_connection()

            # Set the new communication mode
            comm_handler.set_mode(selected_method)

            # Provide feedback to the user
            return f"Communication method set to {selected_method}"
        else:
            # Handle any invalid selection gracefully
            return "Invalid communication method selected."

