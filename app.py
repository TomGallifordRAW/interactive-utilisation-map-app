###############################################################
# EV CHARGER PERFORMANCE MAP DASHBOARD
# Built using Dash, Pandas, and Folium
###############################################################

import os
import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
import folium
import xml.etree.ElementTree as ET
import base64
import io

###############################################################
# STEP 1: LOAD AND PREPROCESS DATA
###############################################################

# Use relative path for CSV (Azure-compatible)
CSV_PATH = os.path.join(os.path.dirname(__file__), 'data', 'Key_Accounts_Map_Data.csv')

# Load CSV
df = pd.read_csv(CSV_PATH)
df.columns = df.columns.str.strip()
df['Venue Type'] = df['Venue Type'].replace({'Hub +': 'Hub+'}).str.strip()
df['Charger Type'] = df['Charger Type'].str.replace(' ', '').str.strip()
df['Energy Utilisation (%)'] = (
    df['Energy Utilisation (%)']
    .astype(str)
    .str.replace('%', '', regex=False)
    .astype(float)
)

df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

# List of key filters
venue_list = sorted(df['Venue Type'].unique())
charger_list = sorted(df['Charger Type'].unique())
account_list = sorted(df['Account'].unique())
location_list = sorted(df['Location'].unique())
port_list = sorted(df['Number of Ports'].unique())

###############################################################
# STEP 2: DEFINE BASELINES AND COLORING LOGIC
###############################################################

baselines = {
    'Sessions/port/day': {
        'Pub': {'AC': [0, 0.15, 0.3, 0.45],
                'DC50': [0, 0.75, 1.5, 2.25],
                'DC150': [0, 1.75, 3.5, 5.25],
                'DC300': [0, 2, 4, 6]},
        'Hotel': {'AC': [0, 0.35, 0.7, 1.05],
                  'DC50': [0, 0.75, 1.5, 2.25],
                  'DC150': [0, 1.75, 3.5, 5.25],
                  'DC300': [0, 2, 4, 6]},
        'Leisure': {'AC': [0, 0.25, 0.5, 0.75],
                    'DC50': [0, 0.75, 1.5, 2.25],
                    'DC150': [0, 1.75, 3.5, 5.25],
                    'DC300': [0, 2, 4, 6]},
        'Attraction': {'AC': [0, 0.45, 0.9, 1.35],
                       'DC50': [0, 0.75, 1.5, 2.25],
                       'DC150': [0, 1.75, 3.5, 5.25],
                       'DC300': [0, 2, 4, 6]},
        'Heritage': {'AC': [0, 0.25, 0.5, 0.75],
                     'DC50': [0, 0.75, 1.5, 2.25],
                     'DC150': [0, 1.75, 3.5, 5.25],
                     'DC300': [0, 2, 4, 6]},
        'Retail': {'AC': [0, 0.95, 1.9, 2.85],
                   'DC50': [0, 0.75, 1.5, 2.25],
                   'DC150': [0, 1.75, 3.5, 5.25],
                   'DC300': [0, 2, 4, 6]},
        'Hub+': {'AC': [0, 0.8, 1.6, 2.4],
                 'DC50': [0, 0.75, 1.5, 2.25],
                 'DC150': [0, 1.75, 3.5, 5.25],
                 'DC300': [0, 2, 4, 6]}
    },
    'Energy Throughput/port/day (kWh)': {
        'Pub': {'AC': [0, 2.5, 5, 7.5],
                'DC50': [0, 19.2, 38.4, 57.6],
                'DC150': [0, 56.7, 113.4, 170.1],
                'DC300': [0, 112.5, 225, 337.5]},
        'Hotel': {'AC': [0, 7.5, 15, 22.5],
                  'DC50': [0, 19.2, 38.4, 57.6],
                  'DC150': [0, 56.7, 113.4, 170.1],
                  'DC300': [0, 112.5, 225, 337.5]},
        'Leisure': {'AC': [0, 4, 8, 12],
                    'DC50': [0, 19.2, 38.4, 57.6],
                    'DC150': [0, 56.7, 113.4, 170.1],
                    'DC300': [0, 112.5, 225, 337.5]},
        'Attraction': {'AC': [0, 7.5, 15, 22.5],
                       'DC50': [0, 19.2, 38.4, 57.6],
                       'DC150': [0, 56.7, 113.4, 170.1],
                       'DC300': [0, 112.5, 225, 337.5]},
        'Heritage': {'AC': [0, 4, 8, 12],
                     'DC50': [0, 19.2, 38.4, 57.6],
                     'DC150': [0, 56.7, 113.4, 170.1],
                     'DC300': [0, 112.5, 225, 337.5]},
        'Retail': {'AC': [0, 11.5, 23, 34.5],
                   'DC50': [0, 19.2, 38.4, 57.6],
                   'DC150': [0, 56.7, 113.4, 170.1],
                   'DC300': [0, 112.5, 225, 337.5]},
        'Hub+': {'AC': [0, 13, 26, 39],
                 'DC50': [0, 19.2, 38.4, 57.6],
                 'DC150': [0, 56.7, 113.4, 170.1],
                 'DC300': [0, 112.5, 225, 337.5]}
    },
    'Energy Utilisation (%)': {
        'Pub': {'AC': [0.00, 1.05, 2.10, 3.15],
                'DC50': [0.00, 3.15, 6.30, 9.45],
                'DC150': [0.00, 3.15, 6.30, 9.45],
                'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Hotel': {'AC': [0.00, 2.80, 5.60, 8.40],
                  'DC50': [0.00, 3.15, 6.30, 9.45],
                  'DC150': [0.00, 3.15, 6.30, 9.45],
                  'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Leisure': {'AC': [0.00, 1.50, 3.00, 4.50],
                    'DC50': [0.00, 3.15, 6.30, 9.45],
                    'DC150': [0.00, 3.15, 6.30, 9.45],
                    'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Attraction': {'AC': [0.00, 2.90, 5.80, 8.70],
                       'DC50': [0.00, 3.15, 6.30, 9.45],
                       'DC150': [0.00, 3.15, 6.30, 9.45],
                       'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Heritage': {'AC': [0.00, 1.50, 3.00, 4.50],
                     'DC50': [0.00, 3.15, 6.30, 9.45],
                     'DC150': [0.00, 3.15, 6.30, 9.45],
                     'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Retail': {'AC': [0.00, 4.40, 8.80, 13.20],
                   'DC50': [0.00, 3.15, 6.30, 9.45],
                   'DC150': [0.00, 3.15, 6.30, 9.45],
                   'DC300': [0.00, 1.85, 3.70, 5.55]},
        'Hub+': {'AC': [0.00, 5.00, 10.00, 15.00],
                 'DC50': [0.00, 3.15, 6.30, 9.45],
                 'DC150': [0.00, 3.15, 6.30, 9.45],
                 'DC300': [0.00, 1.85, 3.70, 5.55]}
    },
    'Net Rev Exc. VAT/port/day': {
        'Pub': {'AC': [0, 1.15, 2.29, 3.44],
                'DC50': [0, 10.41, 20.81, 31.22],
                'DC150': [0, 30.73, 61.46, 92.19],
                'DC300': [0, 60.94, 121.88, 182.81]},
        'Hotel': {'AC': [0, 3.13, 6.26, 9.38],
                  'DC50': [0, 10.41, 20.81, 31.22],
                  'DC150': [0, 30.73, 61.46, 92.19],
                  'DC300': [0, 60.94, 121.88, 182.81]},
        'Leisure': {'AC': [0, 1.83, 3.66, 5.50],
                    'DC50': [0, 10.41, 20.81, 31.22],
                    'DC150': [0, 30.73, 61.46, 92.19],
                    'DC300': [0, 60.94, 121.88, 182.81]},
        'Attraction': {'AC': [0, 3.44, 6.87, 10.31],
                       'DC50': [0, 10.41, 20.81, 31.22],
                       'DC150': [0, 30.73, 61.46, 92.19],
                       'DC300': [0, 60.94, 121.88, 182.81]},
        'Heritage': {'AC': [0, 1.83, 3.66, 5.50],
                     'DC50': [0, 10.41, 20.81, 31.22],
                     'DC150': [0, 30.73, 61.46, 92.19],
                     'DC300': [0, 60.94, 121.88, 182.81]},
        'Retail': {'AC': [0, 5.27, 10.53, 15.80],
                   'DC50': [0, 10.41, 20.81, 31.22],
                   'DC150': [0, 30.73, 61.46, 92.19],
                   'DC300': [0, 60.94, 121.88, 182.81]},
        'Hub+': {'AC': [0, 5.95, 11.91, 17.86],
                 'DC50': [0, 10.41, 20.81, 31.22],
                 'DC150': [0, 30.73, 61.46, 92.19],
                 'DC300': [0, 60.94, 121.88, 182.81]}
    }
}

rating_colors = {'Excellent': 'green', 'Good': 'orange', 'Bad': 'red', 'Critical': 'darkred'}

def get_rating(param, venue, charger, value):
    try:
        bounds = baselines[param][venue][charger]
    except KeyError:
        return 'Critical'
    
    if value >= bounds[3]:
        return 'Excellent'
    elif value >= bounds[2]:
        return 'Good'
    elif value >= bounds[1]:
        return 'Bad'
    else:
        return 'Critical'

# Map account names to relative SVG paths in static/icons/
account_icons = {
    'Greene King': 'GK_Crown_Icon.svg',
    'NT': 'NT_Acorn_Icon.svg',
    'Aberdeen': 'Aberdeen_A_Icon.svg',
    'Aviva': 'Aviva_Sun_Icon.svg',
    'Bespoke': 'Bespoke_House_Icon.svg',
    'MAG': 'MAG_Shopping_Bag_Icon.svg',
    'Merlin': 'Merlin_M_Icon.svg',
    "St George's": 'St_Georges_Triangle_Icon.svg',
    'J27': 'J27_Square_Icon.svg'
}

def get_svg_icon_with_fill(svg_filename, fill_color):
    """
    Read SVG from static/icons/ folder, modify fill color, and return as base64 data URI.
    """
    svg_path = os.path.join(os.path.dirname(__file__), 'static', 'icons', svg_filename)
    
    try:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Modify fill colors in SVG
        for elem in root.iter():
            if 'fill' in elem.attrib and elem.attrib['fill'] != 'none':
                elem.attrib['fill'] = fill_color
        
        # Convert to base64
        out_io = io.BytesIO()
        tree.write(out_io, encoding='utf-8', xml_declaration=True)
        svg_bytes = out_io.getvalue()
        b64 = base64.b64encode(svg_bytes).decode('utf-8')
        
        return f'data:image/svg+xml;base64,{b64}'
    except Exception as e:
        print(f"Error loading SVG {svg_filename}: {e}")
        return None

###############################################################
# STEP 3: BUILD DASH LAYOUT
###############################################################

app = dash.Dash(__name__)
app.title = "EV Charging Performance Map"

app.layout = html.Div([
    html.H2("EV Charger Performance Map"),
    html.Div([
        html.Label('Venue Type'),
        dcc.Dropdown(
            id='venue_filter',
            options=[{'label': v, 'value': v} for v in venue_list],
            placeholder='Select Venue Type',
            clearable=True,
            multi=True
        ),
        html.Label('Charger Type'),
        dcc.Dropdown(
            id='charger_filter',
            options=[{'label': c, 'value': c} for c in charger_list],
            placeholder='Select Charger Type',
            clearable=True,
            multi=True
        ),
        html.Label('Account'),
        dcc.Dropdown(
            id='account_filter',
            options=[{'label': a, 'value': a} for a in account_list],
            placeholder='Select Account',
            clearable=True,
            multi=True
        ),
        html.Label('Location'),
        dcc.Dropdown(
            id='location_filter',
            options=[{'label': l, 'value': l} for l in location_list],
            placeholder='Select Location',
            clearable=True,
            multi=True
        ),
        html.Label('Number of Ports'),
        dcc.Dropdown(
            id='port_filter',
            options=[{'label': n, 'value': n} for n in port_list],
            placeholder='Select Number of Ports',
            clearable=True,
            multi=True
        ),
        html.Label('Parameter for Performance Comparison'),
        dcc.Dropdown(
            id='parameter_filter',
            options=[
                {'label': 'Sessions/port/day', 'value': 'Sessions/port/day'},
                {'label': 'Energy Throughput/port/day (kWh)', 'value': 'Energy Throughput/port/day (kWh)'},
                {'label': 'Energy Utilisation (%)', 'value': 'Energy Utilisation (%)'},
                {'label': 'Net Rev Exc. VAT/port/day', 'value': 'Net Rev Exc. VAT/port/day'}
            ],
            placeholder='(Optional) Select a parameter to color markers by performance',
            clearable=True
        ),
        html.Button('Apply Filters', id='apply_button', n_clicks=0)
    ], style={
        'width': '25%',
        'float': 'left',
        'padding': '15px',
        'backgroundColor': '#f7f7f7',
        'borderRight': '2px solid #ddd'
    }),
    html.Div([
        html.Iframe(id='map', srcDoc="", width='100%', height='700')
    ], style={'width': '70%', 'display': 'inline-block', 'marginLeft': '30px'})
])

###############################################################
# STEP 4: DEFINE CALLBACK FOR FILTERING MAP VIEW
###############################################################

@app.callback(
    Output('map', 'srcDoc'),
    Input('apply_button', 'n_clicks'),
    State('venue_filter', 'value'),
    State('charger_filter', 'value'),
    State('account_filter', 'value'),
    State('location_filter', 'value'),
    State('port_filter', 'value'),
    State('parameter_filter', 'value'),
    prevent_initial_call=True
)
def update_map(n_clicks, venue, charger, account, location, number_of_ports, parameter):
    # Start with empty map
    base_map = folium.Map(
        location=[df['Latitude'].mean(), df['Longitude'].mean()],
        zoom_start=6
    )
    
    # When no filters selected, keep empty map
    if n_clicks == 0 or not any([venue, charger, account, location]):
        return base_map._repr_html_()
    
    # Apply filters
    filtered = df.copy()
    if venue:
        filtered = filtered[filtered['Venue Type'].isin(venue)]
    if charger:
        filtered = filtered[filtered['Charger Type'].isin(charger)]
    if account:
        filtered = filtered[filtered['Account'].isin(account)]
    if location:
        filtered = filtered[filtered['Location'].isin(location)]
    if number_of_ports:
        filtered = filtered[filtered['Number of Ports'].isin(number_of_ports)]
    
    # Add markers
    for _, row in filtered.iterrows():
        popup = '<br>'.join(f'{col}: {row[col]}' for col in filtered.columns
                            if col not in ['Latitude', 'Longitude', 'Postcode'])
        
        color = 'blue'  # default color
        
        # Color-code if parameter selected
        if parameter:
            try:
                val = float(row[parameter])
                rating = get_rating(parameter, row['Venue Type'], row['Charger Type'], val)
                color = rating_colors[rating]
            except:
                color = 'gray'
        
        # Get account name
        account_name = row['Account']
        if isinstance(account_name, list):
            account_name = account_name[0]
        
        # Try to load custom SVG icon
        icon_filename = account_icons.get(account_name)
        icon = None
        
        if icon_filename:
            icon_url = get_svg_icon_with_fill(icon_filename, color)
            if icon_url:
                # Adjust size and anchor for specific accounts
                icon_size = (15, 15)
                icon_anchor = (7.5, 7.5)
                
                if account_name in ['Greene King', 'Bespoke', 'Aviva']:
                    icon_size = (30, 30)
                    icon_anchor = (15, 15)
                elif account_name in ["St George's", 'J27']:
                    icon_size = (27.5, 27.5)
                    icon_anchor = (13.75, 13.75)
                
                icon = folium.CustomIcon(
                    icon_url,
                    icon_size=icon_size,
                    icon_anchor=icon_anchor
                )
        
        # Fall back to simple colored marker if no custom icon
        if not icon:
            icon = folium.Icon(color=color)
        
        # Add marker to map
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup, max_width=300),
            icon=icon
        ).add_to(base_map)
    
    return base_map._repr_html_()

###############################################################
# STEP 5: RUN THE APP
###############################################################
server = app.server

if __name__ == '__main__':
    # Get port from environment variable (Azure sets PORT env var)
    port = int(os.environ.get('PORT', 8000))
    
    # Set debug=False for production
    app.run(debug=False, host='0.0.0.0', port=port)