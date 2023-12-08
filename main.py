from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from config import DevelopmentConfig, Config
from eia_api import EIA_API
from utilities import create_graph, create_combined_graph, normalize_data, calculate_projections, calculate_state_increase
import json
import webbrowser
from datetime import datetime, timedelta
from state_mappings import state_name_to_abbr
import os
from database import Database
import copy

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

# Initialize EIA API with API key
api_key = Config.API_KEY
eia_api = EIA_API(api_key)

# Load GeoJSON data for states
with open('static/states.json', 'r') as file:
    states_geojson = json.load(file)

non_plottable_fields = ['id', 'state', 'stateDescription', 'period', 'facility_direct']  

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/fetch_data', methods=['POST'])
def fetch_data():
    start_date = request.form['start_year']
    end_date = request.form['end_year']  # If you have an end year selection

    # Construct the dates
    if len(start_date) < 7:
        start_date = f"{start_date}-01-01"
        end_date = f"{end_date}-12-31"

    # Store dates in the session
    session['date_range'] = (start_date, end_date)
    # Fetch and store data based on the provided dates
    eia_api.fetch_and_store_data(start_date, end_date)
    return redirect(url_for('select_states'))

@app.route('/select_states', methods=['GET', 'POST'])
def select_states():
    if request.method == 'POST':
        # Process selected states and redirect
        session['selected_states'] = request.form.getlist('states')
        return redirect(url_for('select_features'))

    with Database('eia_data.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT state FROM eia_data ORDER BY state ASC")
        states = [row[0] for row in cursor.fetchall()]

    # Add "US", "District of Columbia", and "Puerto Rico" to the states list
    additional_states = ['Puerto Rico'] #['US', 'District of Columbia', 'Puerto Rico']
    states.extend(additional_states)
    
    # Sort the states alphabetically, including the additional states
    # Translate full state names to abbreviations
    abbreviated_states = [state_name_to_abbr.get(state, state) for state in states]

    # Sort the states alphabetically
    abbreviated_states = sorted(abbreviated_states)

    return render_template('select_states.html', states=abbreviated_states)

@app.route('/select_features', methods=['GET'])
def select_features():
    selected_states = session.get('selected_states', [])

    with Database('eia_data.db') as conn:
        cursor = conn.cursor()
        columns = []
        if selected_states:
            placeholders = ', '.join('?' for _ in selected_states)
            cursor.execute(f"SELECT * FROM eia_data WHERE state IN ({placeholders}) LIMIT 1", selected_states)
            # Extracting column names and filtering out non-plottable fields
            columns = [description[0] for description in cursor.description if description[0] not in non_plottable_fields and '_units' not in description[0]]

    # Sort the columns (elements) alphabetically
    columns = sorted(columns)
    
    return render_template('select_features.html', features=columns)

@app.route('/get_data_for_graphs')
def get_data_for_graphs():
    graphs_data = []

    with Database('eia_data.db') as conn:
        cursor = conn.cursor()
        # Fetch columns with data for plotting
        cursor.execute("SELECT * FROM eia_data LIMIT 1")
        columns = [description[0] for description in cursor.description if description[0] != 'id' and description[0] != 'period']
        
        for column in columns:
            cursor.execute(f"SELECT period, \"{column}\" FROM eia_data WHERE \"{column}\" IS NOT NULL ORDER BY period")
            data = cursor.fetchall()
            x_values = [row[0] for row in data]
            y_values = [row[1] for row in data]

            graphs_data.append({
                'x': x_values,
                'y': y_values,
                'series_name': column,
                'graph_title': f"Graph of {column}"
            })
            
    return jsonify(graphs_data)

@app.route('/create_graphs', methods=['POST'])
def create_graphs():
    selected_features = request.form.getlist('features')
    selected_states = session.get('selected_states', [])
    start_date, end_date = session.get('date_range', (None, None))
    start_date_str = "1990-01-01"
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    start_date = start_date - timedelta(days=365)
    units_fields = session.get('units_fields', {})

    # Reverse the state_name_to_abbr dictionary
    abbr_to_state_name = {v: k for k, v in state_name_to_abbr.items()}

    # Translate abbreviations to full names
    selected_states_full_names = [abbr_to_state_name.get(state_abbr, state_abbr) for state_abbr in selected_states]

    graph_heatmap_pairs = []

    for feature_name in selected_features:
        # Initialize a set to track processed states for this feature
        processed_states = set()
        series_data = []
        for state in selected_states:
            if state not in processed_states:
                processed_states.add(state)
                # Fetch the data from the database for each state and feature
                query = """
                    SELECT period, SUM("{}") AS aggregated_value
                    FROM eia_data
                    WHERE state = ? AND period BETWEEN ? AND ?
                    AND "{}" IS NOT NULL
                    GROUP BY period
                    ORDER BY period
                """.format(feature_name, feature_name)
                
                with Database(eia_api.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute(query, (state, start_date, end_date))
                    data = cursor.fetchall()

                periods = [row[0] for row in data]
                values = [row[1] for row in data]
                
                series_data.append({'x': periods, 'y': values, 'name': state})

        # Sort the series_data based on the last y-value of each series
        series_data.sort(key=lambda s: s['y'][-1] if s['y'] else 0, reverse=True)

        # Process heatmaps and create graph
        increase_data = eia_api.calculate_increase_for_feature(feature_name, start_date, end_date)
        normalized_data = normalize_data(increase_data)
        feature_geojson = copy.deepcopy(states_geojson)
        feature_geojson['features'] = [
            feature for feature in feature_geojson['features']
            if feature['properties']['NAME'] in selected_states_full_names
        ]
        
        for feature in feature_geojson['features']:
            state_abbr = state_name_to_abbr.get(feature['properties']['NAME'])
            feature['properties']['increaseValue'] = normalized_data.get(state_abbr, 0)

        graph_html = create_combined_graph(series_data, feature_name, units_fields.get(feature_name, 'Value'), include_projections=True)
        graph_heatmap_pairs.append((graph_html, feature_geojson, feature_name))

    return render_template('dashboard.html', graph_heatmap_pairs=graph_heatmap_pairs)

@app.route('/dashboard', methods=['POST', 'GET'])
def dashboard():
    selected_elements = session.get('selected_elements', [])
    selected_states = session.get('selected_states', [])
    start_date, end_date = session.get('date_range', (None, None))
    units_fields = session.get('units_fields', {})
    graphs = []

    if request.method == 'POST':
        selected_elements = session.get('selected_elements', [])
        start_date, end_date = session.get('date_range', (None, None))
        
        # Calculate increases for all selected elements
        for element in selected_elements:
            increase_data = eia_api.calculate_increase_for_element(element, start_date, end_date)
            normalized_data = normalize_data(increase_data)

            # Update the GeoJSON with the new 'increaseValue' property
            for feature in states_geojson['features']:
                state = feature['properties']['NAME']
                
                feature['properties']['increaseValue'] = normalized_data.get(state, 0)         
    
    with Database(eia_api.db_path) as conn:
        cursor = conn.cursor()

        for state in selected_states:
            for element in selected_elements:
                y_axis_label = units_fields.get(element, 'Value')  # Retrieve the unit

                query = f"""
                    SELECT period, SUM(\"{element}\") AS aggregated_value FROM eia_data 
                    WHERE state = ? AND period BETWEEN ? AND ? 
                    AND \"{element}\" IS NOT NULL 
                    GROUP BY period
                    ORDER BY period
                """
                
                cursor.execute(query, (state, start_date, end_date))
                data = cursor.fetchall()

                x_values = [row[0] for row in data]
                y_values = [row[1] for row in data]

                graph_title = f"{element} in {state} ({start_date} - {end_date})"
                graph = create_graph(x_values, y_values, element, "Graph Title", y_axis_label)  # Include y_axis_label
                graphs.append(graph)
    
    return render_template('dashboard.html', graphs=graphs, geojson_data=json.dumps(states_geojson))

if __name__ == '__main__':
    # Fetch sample data only when not in reloader process
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        eia_api.fetch_and_store_data(fetch_sample=True)
        webbrowser.open_new('http://127.0.0.1:5000/')
    
    app.run()
