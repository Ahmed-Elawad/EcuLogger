import os
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go

# Function to read the CSV file
def read_csv(file_path):
    encoding = 'utf-16'  # Try 'utf-16-le' or 'utf-16-be' if needed

    # Read column names and units
    col_names = pd.read_csv(file_path, nrows=0, encoding=encoding).columns.tolist()
    units = pd.read_csv(file_path, skiprows=0, nrows=1, header=None, encoding=encoding).iloc[0].tolist()

    # Read data starting from the third row
    data = pd.read_csv(file_path, skiprows=2, header=None, encoding=encoding)
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

# Get the list of CSV files in the current directory
csv_files = [f for f in os.listdir('.') if f.endswith('.csv')]

# Updated measurement_types dictionary
measurement_types = {
    'Boost pressure': 'Pressure',
    'Engine oil pressure': 'Pressure',
    'Fuel pressure (Measured)': 'Pressure',
    'Fuel pressure (Calculated)': 'Pressure',
    'Engine oil level': 'Volume',
    'Engine oil level_2': 'Distance',
    'Cam position': 'Angle',
    'Spark advance': 'Angle',
    'Spark advance (calculated)': 'Angle',
    'Spark advance reduction (Cyl. 1)': 'Angle',
    'Spark advance reduction (Cyl. 2)': 'Angle',
    'Spark advance reduction (Cyl. 3)': 'Angle',
    'Spark advance reduction (Cyl. 4)': 'Angle',
    'Battery voltage': 'Voltage',
    'Vehicle speed': 'Speed',
    'Engine speed': 'Rotational Speed',
    'Engine temperature': 'Temperature',
    'Air temperature': 'Temperature',
    'Air temperature (Boost/Manifold)': 'Temperature',
    'Engine oil temperature': 'Temperature',
    'UniAir oil temperature': 'Temperature',
    'Injection time': 'Time',
    'Injection time correction': 'Time',
    'Coil 1 charge time': 'Time',
    'Coil 2 charge time': 'Time',
    'Coil 3 charge time': 'Time',
    'Coil 4 charge time': 'Time',
    'Knock sensor signal': 'Signal',
    'Knock sensor signal (Cyl. 1)': 'Signal',
    'Knock sensor signal (Cyl. 2)': 'Signal',
    'Knock sensor signal (Cyl. 3)': 'Signal',
    'TAG': 'Identifier',  # Assuming TAG is an identifier without units
    # Add other columns as necessary
}

# Updated unit_conversions dictionary
unit_conversions = {
    'Pressure': {
        'bar': {
            'bar': lambda x: x,
            'mbar': lambda x: x * 1000,
            'psi': lambda x: x * 14.5038,
        },
        'mbar': {
            'bar': lambda x: x / 1000,
            'mbar': lambda x: x,
            'psi': lambda x: x * 0.0145038,
        },
        'psi': {
            'bar': lambda x: x / 14.5038,
            'mbar': lambda x: x * 68.9476,
            'psi': lambda x: x,
        },
    },
    'Volume': {
        'l': {
            'l': lambda x: x,
            'ml': lambda x: x * 1000,
            'gal': lambda x: x * 0.264172,
        },
        'ml': {
            'l': lambda x: x / 1000,
            'ml': lambda x: x,
            'gal': lambda x: x * 0.000264172,
        },
        'gal': {
            'l': lambda x: x / 0.264172,
            'ml': lambda x: x * 3785.41,
            'gal': lambda x: x,
        },
    },
    'Distance': {
        'mm': {
            'mm': lambda x: x,
            'cm': lambda x: x / 10,
            'm': lambda x: x / 1000,
            'inch': lambda x: x / 25.4,
        },
        'cm': {
            'mm': lambda x: x * 10,
            'cm': lambda x: x,
            'm': lambda x: x / 100,
            'inch': lambda x: x / 2.54,
        },
        'm': {
            'mm': lambda x: x * 1000,
            'cm': lambda x: x * 100,
            'm': lambda x: x,
            'inch': lambda x: x * 39.3701,
        },
        'inch': {
            'mm': lambda x: x * 25.4,
            'cm': lambda x: x * 2.54,
            'm': lambda x: x / 39.3701,
            'inch': lambda x: x,
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
    'Voltage': {
        'V': {
            'V': lambda x: x,
            'mV': lambda x: x * 1000,
        },
        'mV': {
            'V': lambda x: x / 1000,
            'mV': lambda x: x,
        },
    },
    'Speed': {
        'km/h': {
            'km/h': lambda x: x,
            'm/s': lambda x: x / 3.6,
            'mph': lambda x: x * 0.621371,
        },
        'm/s': {
            'km/h': lambda x: x * 3.6,
            'm/s': lambda x: x,
            'mph': lambda x: x * 2.23694,
        },
        'mph': {
            'km/h': lambda x: x / 0.621371,
            'm/s': lambda x: x / 2.23694,
            'mph': lambda x: x,
        },
    },
    'Rotational Speed': {
        'RPM': {
            'RPM': lambda x: x,
            'Hz': lambda x: x / 60,
        },
        'Hz': {
            'RPM': lambda x: x * 60,
            'Hz': lambda x: x,
        },
    },
    'Temperature': {
        '°C': {
            '°C': lambda x: x,
            '°F': lambda x: (x * 9/5) + 32,
            'K': lambda x: x + 273.15,
        },
        '°F': {
            '°C': lambda x: (x - 32) * 5/9,
            '°F': lambda x: x,
            'K': lambda x: ((x - 32) * 5/9) + 273.15,
        },
        'K': {
            '°C': lambda x: x - 273.15,
            '°F': lambda x: ((x - 273.15) * 9/5) + 32,
            'K': lambda x: x,
        },
    },
    'Time': {
        'ms': {
            'ms': lambda x: x,
            's': lambda x: x / 1000,
        },
        's': {
            'ms': lambda x: x * 1000,
            's': lambda x: x,
        },
    },
    'Signal': {
        'unit': {
            'unit': lambda x: x,
        },
    },
    'Identifier': {
        'none': {
            'none': lambda x: x,
        },
    },
    # Add other measurement types and units as needed
}

# Initialize the Dash app
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = 'Interactive Data Grapher'

# Function to get the left panel
def get_left_panel():
    return html.Div(
        id='left-panel',
        children=[
            html.Label('Select CSV File:'),
            dcc.Dropdown(
                id='file-selector',
                options=[{'label': f, 'value': f} for f in csv_files],
                value=csv_files[0] if csv_files else None,
                clearable=False
            ),
            html.Hr(),
            html.Label('Select Data Series to Display:'),
            dcc.Checklist(
                id='data-series-selector',
                options=[],
                value=[],
                inputStyle={'margin-right': '5px'},
                labelStyle={'display': 'block'}
            ),
            html.Hr(),
            html.Label('Select Units:'),
            # Unit selection dropdowns will be dynamically generated
            html.Div(id='unit-selectors')
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

# Callback to update data series options when a file is selected
@app.callback(
    [Output('data-series-selector', 'options'),
     Output('data-series-selector', 'value'),
     Output('unit-selectors', 'children'),
     Output('stored-data', 'data')],
    [Input('file-selector', 'value')]
)
def update_data_series(file_path):
    if not file_path:
        return [], [], [], {}
    # Read the selected CSV file
    data, col_labels, unit_labels = read_csv(file_path)
    # Get the list of columns excluding the time column
    time_column = col_labels[0]
    data_columns = col_labels[1:]
    # Store data and labels in a dictionary to share between callbacks
    stored_data = {
        'data': data.to_dict(),
        'col_labels': col_labels,
        'unit_labels': unit_labels,
        'time_column': time_column,
        'data_columns': data_columns
    }
    # Update the data series options
    data_series_options = [{'label': col, 'value': col} for col in data_columns]
    data_series_value = data_columns  # Select all by default

    # Generate unit selectors based on measurement types
    measurement_type_list = list(set(measurement_types.values()))
    unit_selectors = [
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
        ]) for measurement_type in measurement_type_list
    ]
    return data_series_options, data_series_value, unit_selectors, stored_data

# Store data in dcc.Store to share between callbacks
app.layout.children.append(dcc.Store(id='stored-data'))

# Callback to update the graph based on selected data series and units
@app.callback(
    Output('data-graph', 'figure'),
    [Input('data-series-selector', 'value'),
     Input('panel-state', 'data')] +
    [Input(f'unit-selector-{mt}', 'value') for mt in set(measurement_types.values())],
    [State('stored-data', 'data')]
)
def update_graph(*args):
    selected_series = args[0]
    panel_state = args[1]
    unit_selections = args[2:-1]  # All args except the first two and the last one
    stored_data = args[-1]

    if not stored_data:
        return go.Figure()

    data = pd.DataFrame(stored_data['data'])
    col_labels = stored_data['col_labels']
    unit_labels = stored_data['unit_labels']
    time_column = stored_data['time_column']
    data_columns = stored_data['data_columns']

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
        original_unit = unit_labels.get(series_name, None)
        measurement_type = measurement_types.get(series_name, None)

        y_data = data[series]
        y_label = series

        # Apply unit conversion if applicable
        if measurement_type in unit_conversions and original_unit in unit_conversions[measurement_type]:
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
