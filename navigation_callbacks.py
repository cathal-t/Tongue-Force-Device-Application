from dash import Input, Output

def register_callbacks(app):
    @app.callback(
        Output('url', 'pathname'),
        [Input('max-force-button', 'n_clicks'),
         Input('calibration-button', 'n_clicks'),
         Input('arcade-button', 'n_clicks')]
    )
    def navigate_pages(max_force_clicks, calibration_clicks, arcade_clicks):
        if max_force_clicks > 0:
            return '/max-force-test'
        elif calibration_clicks > 0:
            return '/calibration'
        elif arcade_clicks > 0:
            return '/arcade'
        return '/'
