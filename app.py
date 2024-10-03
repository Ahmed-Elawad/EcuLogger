import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Function to read the CSV file
def read_csv(file_path):
    # Read column names and units
    col_names = pd.read_csv(file_path, nrows=0).columns.tolist()
    units = pd.read_csv(file_path, skiprows=0, nrows=1, header=None).iloc[0].tolist()

    # Read data starting from the third row
    data = pd.read_csv(file_path, skiprows=2, header=None)
    data.columns = col_names

    # Handle duplicate column names by appending a counter
    from collections import Counter
    counts = Counter()
    col_labels = []
    unit_labels = {}
    for name, unit in zip(col_names, units):
        counts[name] += 1
        if counts[name] > 1:
            name_unique = f"{name}_{counts[name]}"
        else:
            name_unique = name
        label = f"{name_unique} ({unit})"
        col_labels.append(label)
        unit_labels[name_unique] = unit  # Store units with unique names
    data.columns = col_labels
    return data, col_labels, unit_labels

# Replace 'Sample.csv' with your CSV file path
data, col_labels, unit_labels = read_csv('Sample.csv')

# Map columns to measurement types
measurement_types = {
    'Boost pressure': 'Pressure',
    'Engine oil pressure': 'Pressure',
    'Engine oil level': 'Volume',
    'Engine oil level_2': 'Distance',
    'Cam position': 'Angle',
    # Add other columns as necessary
}

# Unit conversion mappings (as before)
unit_conversions = {
    'Pressure': {
        'bar': {
            'bar': lambda x: x,
            'mbar': lambda x: x * 1000,
        },
        'mbar': {
            'bar': lambda x: x / 1000,
            'mbar': lambda x: x,
        },
    },
    'Volume': {
        'l': {
            'l': lambda x: x,
            'ml': lambda x: x * 1000,
        },
        'ml': {
            'l': lambda x: x / 1000,
            'ml': lambda x: x,
        },
    },
    'Distance': {
        'mm': {
            'mm': lambda x: x,
            'cm': lambda x: x / 10,
            'm': lambda x: x / 1000,
        },
        'cm': {
            'mm': lambda x: x * 10,
            'cm': lambda x: x,
            'm': lambda x: x / 100,
        },
        'm': {
            'mm': lambda x: x * 1000,
            'cm': lambda x: x * 100,
            'm': lambda x: x,
        },
    },
    'Angle': {
        'deg.': {
            'deg.': lambda x: x,
            'rad': lambda x: x * (3.141592653589793 / 180),
        },
        'rad': {
            'deg.': lambda x: x * (180 / 3.141592653589793),
            'rad': lambda x: x,
        },
    },
    # Add other measurement types and units as needed
}

# Get the list of columns excluding the time column
time_column = col_labels[0]
data_columns = col_labels[1:]

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = 'Interactive Data Grapher'

# Function to get the left panel
def get_left_panel():
    return html.Div(
        id='left-panel',
        children=[
            html.Label('Select Data Series to Display:'),
            dcc.Checklist(
                id='data-series-selector',
                options=[{'label': col, 'value': col} for col in data_columns],
                value=data_columns,
                inputStyle={'margin-right': '5px'},
                labelStyle={'display': 'block'}
            ),
            html.Hr(),
            html.Label('Select Units:'),
            # Unit selection dropdowns
            *[
                html.Div([
                    html.Label(f'{measurement_type}:'),
                    dcc.Dropdown(
                        id=f'unit-selector-{measurement_type}',
                        options=[
                            {'label': unit, 'value': unit}
                            for unit in unit_conversions[measurement_type][list(unit_conversions[measurement_type].keys())[0]].keys()
                        ],
                        value=list(unit_conversions[measurement_type][list(unit_conversions[measurement_type].keys())[0]].keys())[0],
                    )
                ]) for measurement_type in set(measurement_types.values())
            ]
        ],
        style={'overflowY': 'auto', 'width': '20%', 'display': 'block', 'float': 'left'}
    )

# Layout of the app
app.layout = html.Div([
    html.H1('Interactive Data Grapher'),
    html.Button('Hide Panel', id='toggle-button', n_clicks=0),
    dcc.Store(id='panel-state', data='visible'),
    html.Div([
        get_left_panel(),
        html.Div(
            id='graph-container',
            children=[
                dcc.Graph(
                    id='data-graph',
                    config={'displayModeBar': True},
                    style={'height': '90vh', 'width': '100%'}
                )
            ],
            style={'width': '78%', 'display': 'inline-block', 'float': 'right'}
        )
    ], style={'width': '100%', 'display': 'inline-block'})
])

# Callback to update the panel visibility and button text
@app.callback(
    [Output('left-panel', 'style'),
     Output('graph-container', 'style'),
     Output('toggle-button', 'children'),
     Output('panel-state', 'data')],
    [Input('toggle-button', 'n_clicks')],
    [State('panel-state', 'data')]
)
def toggle_panel(n_clicks, panel_state):
    if panel_state == 'visible':
        # Hide the panel
        left_panel_style = {'display': 'none'}
        graph_container_style = {'width': '98%', 'display': 'inline-block', 'float': 'right'}
        button_text = 'Show Panel'
        panel_state = 'hidden'
    else:
        # Show the panel
        left_panel_style = {'overflowY': 'auto', 'width': '20%', 'display': 'block', 'float': 'left'}
        graph_container_style = {'width': '78%', 'display': 'inline-block', 'float': 'right'}
        button_text = 'Hide Panel'
        panel_state = 'visible'
    return left_panel_style, graph_container_style, button_text, panel_state

# Callback to update the graph based on selected data series and units
@app.callback(
    Output('data-graph', 'figure'),
    [Input('data-series-selector', 'value'),
     Input('panel-state', 'data')] +
    [Input(f'unit-selector-{mt}', 'value') for mt in set(measurement_types.values())]
)
def update_graph(selected_series, panel_state, *unit_selections):
    measurement_type_list = list(set(measurement_types.values()))
    if panel_state == 'hidden':
        # Use default units if panel is hidden
        selected_units = {mt: list(unit_conversions[mt][list(unit_conversions[mt].keys())[0]].keys())[0] for mt in measurement_type_list}
    else:
        # Map measurement types to selected units
        selected_units = dict(zip(measurement_type_list, unit_selections))

    # If no series is selected, avoid errors by showing an empty graph
    if not selected_series:
        selected_series = []
    traces = []
    for series in selected_series:
        # Get the unique column name without the unit
        series_name = series.split(' (')[0]
        original_unit = unit_labels[series_name]
        measurement_type = measurement_types.get(series_name, None)

        y_data = data[series]
        y_label = series

        # Apply unit conversion if applicable
        if measurement_type in unit_conversions:
            desired_unit = selected_units[measurement_type]
            if original_unit != desired_unit:
                try:
                    conversion_func = unit_conversions[measurement_type][original_unit][desired_unit]
                    y_data = y_data.apply(conversion_func)
                    y_label = f"{series_name} ({desired_unit})"
                except KeyError:
                    pass  # Conversion not defined

        traces.append(go.Scatter(
            x=data[time_column],
            y=y_data,
            mode='lines',
            name=y_label
        ))

    layout = go.Layout(
        xaxis={'title': time_column},
        yaxis={'title': 'Value'},
        hovermode='closest',
        height=600  # Adjust the height as needed
    )
    figure = {'data': traces, 'layout': layout}
    return figure

if __name__ == '__main__':
    app.run_server(debug=True)
