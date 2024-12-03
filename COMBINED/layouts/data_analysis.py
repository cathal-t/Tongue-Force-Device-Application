# layouts/data_analysis.py

from dash import html, dcc
import dash_bootstrap_components as dbc

# Common styles
font_family = 'Helvetica, Arial, sans-serif'
box_style = {
    'flex': '1',
    'textAlign': 'left',
    'padding': '20px',
    'backgroundColor': '#f8f8f8',
    'border-radius': '8px',
    'margin': '0 10px',
    'display': 'flex',
    'flexDirection': 'column',
    'font-family': font_family
}
heading_style = {
    'color': '#000',
    'margin-bottom': '5px',
    'font-family': font_family,
    'font-size': '20px',
    'font-weight': 'bold'
}
label_style = {
    'font-family': font_family,
    'font-size': '16px',
    'margin-top': '10px'
}
dropdown_style = {
    'margin-bottom': '20px',
    'font-family': font_family
}
button_style = {
    'margin-bottom': '10px',
    'font-family': font_family,
    'width': '100%',
    'padding': '12px',
    'backgroundColor': '#5783db',
    'font-size': '28px',
    'border-radius': '8px'
}

layout = html.Div([
    html.H1('Data Analysis', style={
        'textAlign': 'center',
        'color': '#000',
        'margin-bottom': '20px',
        'margin-top': '20px',
        'font-family': font_family
    }),

    dbc.Container([
        dbc.Row([
            dbc.Col([
                # Sidebar content
                html.Div([
                    html.H2("Choose Files", style={'textAlign': 'center', 'font-family': font_family}),
                    html.Hr(),
                    html.Label('Select Patient ID', style=label_style),
                    dcc.Dropdown(
                        id='patient-id-dropdown',
                        options=[],  # Options will be populated dynamically
                        placeholder='Search or select a patient ID',
                        style=dropdown_style
                    ),
                    html.Label('Select Session(s)', style=label_style),
                    dcc.Checklist(
                        id='session-checklist',
                        options=[],  # Options will be populated based on selected patient
                        value=[],
                        style={
                            'margin-bottom': '20px',
                            'font-family': font_family
                        }
                    ),
                    html.Label('Select Time Range', style=label_style),
                    # Wrap the RangeSlider in an html.Div with the desired style
                    html.Div(
                        dcc.RangeSlider(
                            id='time-range-slider',
                            min=0,
                            max=10,
                            value=[0, 10],
                            marks={0: '0', 10: '10'},
                            tooltip={"placement": "bottom", "always_visible": True},
                            step=0.1,
                            allowCross=False,
                            disabled=True,  # Initially disabled
                            updatemode='drag',
                        ),
                        style={'margin-bottom': '20px'}
                    ),
                    html.Button('Plot', id='plot-data-button', n_clicks=0,
                                className='btn btn-primary',
                                style=button_style),
                    # Commented out the Export buttons and Download component
                    # html.Div([
                    #     html.Button('Export as PNG', id='export-png-button', n_clicks=0,
                    #                 className='btn btn-secondary',
                    #                 style={
                    #                     'margin-right': '10px',
                    #                     'font-family': font_family,
                    #                     'padding': '10px',
                    #                     'font-size': '16px',
                    #                     'border-radius': '8px'
                    #                 }),
                    #     html.Button('Export as JPEG', id='export-jpeg-button', n_clicks=0,
                    #                 className='btn btn-secondary',
                    #                 style={
                    #                     'margin-right': '10px',
                    #                     'font-family': font_family,
                    #                     'padding': '10px',
                    #                     'font-size': '16px',
                    #                     'border-radius': '8px'
                    #                 }),
                    #     html.Button('Export as PDF', id='export-pdf-button', n_clicks=0,
                    #                 className='btn btn-secondary',
                    #                 style={
                    #                     'font-family': font_family,
                    #                     'padding': '10px',
                    #                     'font-size': '16px',
                    #                     'border-radius': '8px'
                    #                 }),
                    # ], style={'textAlign': 'center', 'margin-top': '20px'}),
                    # dcc.Download(id='download-image'),
                ], style=box_style),
            ], width=3, style={
                'border-right': '1px solid #ddd',
                'padding': '20px',
                'backgroundColor': '#fff'
            }),

            dbc.Col([
                # Main content
                html.Div(
                    dcc.Graph(
                        id='data-analysis-graph',
                        config={'displayModeBar': True},
                        style={
                            'margin-bottom': '20px',
                            'border-radius': '8px',
                            'height': '600px'
                        }
                    ),
                    style={
                        'width': '100%',
                        'margin-left': 'auto',
                        'margin-right': 'auto',
                    }
                ),
            ], width=9, style={'padding': '20px'}),
        ])
    ], fluid=True)
], style={
    'font-family': font_family,
    'backgroundColor': '#f8f8f8'
})
