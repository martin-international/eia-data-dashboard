import numpy as np
import pandas as pd
import pmdarima as pm
from statsmodels.tsa.arima.model import ARIMA
import plotly.graph_objs as go
import concurrent.futures
from database import Database
import eia_api


def normalize_data(data):
    """
    Normalizes the provided data to a range between 0 and 1.
    """
    min_value = min(data.values())
    max_value = max(data.values())

    if min_value == max_value:
        return {key: 0.5 for key in data}

    return {key: (value - min_value) / (max_value - min_value) for key, value in data.items()}

def arima_forecast(historical_values, num_predictions, train_window=10):
    data = pd.Series(historical_values)
    train_data = data[-train_window:]

    # Define lists of values for p, d, and q to try
    p_values = [0, 1]
    d_values = [0, 1]
    q_values = [0, 1]

    best_aic = float('inf')
    best_order = None
    best_model = None

    for p in p_values:
        for d in d_values:
            for q in q_values:
                try:
                    model = pm.ARIMA(order=(p, d, q), suppress_warnings=True)
                    results = model.fit(train_data)
                    aic = results.aic()

                    if aic < best_aic:
                        best_aic = aic
                        best_order = (p, d, q)
                        best_model = results
                    else:
                        # Early termination if AIC starts to increase
                        break  # Break the innermost loop

                except Exception as e:
                    print(f'Exception: {e}')
                    continue

    if best_model is not None:
        # Fit the selected model to the entire dataset
        fitted_model = pm.ARIMA(order=best_order, suppress_warnings=True).fit(data)

        # Forecast future values
        forecast = fitted_model.predict(n_periods=num_predictions)
        return forecast
    else:
        print("No suitable model found.")
        return None

def create_graph(x_values, y_values, feature, graph_title, unit_type):
    y_max = max(y_values) * 1.25  
    y_min = min(y_values) * 0.75  

    fig = go.Figure(go.Bar(
        x=x_values,
        y=y_values,
        name=element  
    ))

    fig.update_layout(
        title=graph_title,
        xaxis=dict(title='Year'),
        yaxis=dict(title=unit_type, range=[y_min, y_max])  # Set the y-axis range based on the data
    )

    return fig.to_html(full_html=False)

def try_calculate_projections(series, max_years):
    for num_years in range(max_years, 0, -1):
        try:
            projections = calculate_projections(series['y'], num_years=num_years)
            return projections  # Return successfully calculated projections
        except Exception as e:
            pass

    # If the loop completes without returning, it means all attempts failed
    raise ValueError(f"Unable to calculate projections for any number of years up to {max_years}")

def process_series(i, series, feature, unit_type, include_projections, projection_years, colors, all_y_values):
    fig = go.Figure()  # Create a separate figure for each series
    # Determine the color for the series
    base_color = '#FF0000' if series['name'] == 'US' else colors[i % len(colors)]

    # Convert to rgba for transparency handling
    transparent_color, opaque_color = hex_to_rgba(base_color)

    # Add existing data to the figure with opaque color
    fig.add_trace(go.Scatter(
        x=series['x'],
        y=series['y'],
        mode='lines+markers',
        name=series['name'],
        line=dict(color=opaque_color)
    ))
    all_y_values.extend(series['y'])

    if include_projections and series['y']:
        try:
            projections = try_calculate_projections(series, max_years=10)
        except ValueError as e:
            print(e)
        if projections:
            # Forecast future values using ARIMA
            future_years = [str(int(series['x'][-1]) + i - 1) for i in range(1, projection_years + 1)]
            forecasted_values = arima_forecast(series['y'], projection_years)

            fig.add_trace(go.Scatter(
                x=future_years,
                y=forecasted_values,
                mode='lines',
                line=dict(color=opaque_color, width=1, dash='dot'),
                name=f"{series['name']} ARIMA projection",
                showlegend=False
            ))
            last_year = int(series['x'][-1])
            fig.add_trace(go.Scatter(
                x=future_years,
                y=projections['upper'],
                mode='lines',
                line=dict(color=transparent_color, width=1, dash='solid'),
                name=f"{series['name']} upper projection",
                showlegend=False,
                hoverlabel=dict(
                    bgcolor=opaque_color, 
                    bordercolor=opaque_color,
                    font=dict(
                        color='white'  
                    )
                ))
            )
            fig.add_trace(go.Scatter(
                x=future_years,
                y=projections['lower'],
                mode='lines',
                fill='tonexty',
                fillcolor=transparent_color,
                line=dict(color=transparent_color, width=1, dash='solid'),
                name=f"{series['name']} lower projection",
                showlegend=False,
                hoverlabel=dict(
                    bgcolor=opaque_color,
                    bordercolor=opaque_color,
                    font=dict(
                        color='white'
                    )
                ))
            )
    return fig
    
def create_combined_graph(series_data, element, unit_type, include_projections=False, projection_years=10):
    fig = go.Figure()
    all_y_values = []
    colors = [
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#F0E442",
    "#0072B2",
    "#D55E00",
    "#CC79A7" 
    ]
    
    fig = go.Figure()

    with concurrent.futures.ThreadPoolExecutor() as executor:  
        futures = []
        for i, series in enumerate(series_data):
            futures.append(executor.submit(
                process_series, i, series, element, unit_type, include_projections, projection_years, colors, all_y_values))

        for future in concurrent.futures.as_completed(futures):
            fig.add_traces(future.result().data)
        
    y_min = min(all_y_values) * 0.75
    y_max = max(all_y_values) * 1.25
    fig.update_layout(
        yaxis=dict(range=[y_min, y_max])
    )

    fig.update_layout(
        title=f"{element} - {unit_type}",
        xaxis=dict(title='Year'),
        yaxis=dict(title=unit_type),
        legend_title="States",
        showlegend=True,
        legend=dict(traceorder='normal')
        )

    return fig.to_html(full_html=False)

def calculate_projections(y_values, num_years=10, num_simulations=1000):
    """
    Calculates future value projections based on historical data.
    """
    if not y_values:
        return None

    yearly_changes = np.diff(y_values)
    mean_change = np.mean(yearly_changes)
    std_dev = np.std(yearly_changes)

    projections = []
    last_value = y_values[-1]

    for _ in range(num_simulations):
        future_values = [last_value]
        for _ in range(num_years + 1):
            future_change = np.random.normal(mean_change, std_dev)
            future_values.append(future_values[-1] + future_change)
        projections.append(future_values)

    projections = np.array(projections)
    lower_band = np.percentile(projections, 2.5, axis=0)
    upper_band = np.percentile(projections, 97.5, axis=0)

    return {'upper': upper_band.tolist(), 'lower': lower_band.tolist()}

def hex_to_rgba(hex_color, opacity=0.2):
    """
    Converts a hex color to rgba format with the specified opacity.
    """
    if hex_color.startswith('#'):
        hex_color = hex_color.lstrip('#')
        return f'rgba({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}, {opacity})', f'rgba({int(hex_color[0:2], 16)}, {int(hex_color[2:4], 16)}, {int(hex_color[4:6], 16)}, 1)'
    elif hex_color.startswith('rgb('):
        rgb_values = hex_color.replace('rgb', '').replace('(', '').replace(')', '').split(',')        
        return f'rgba({", ".join(value.strip() for value in rgb_values)}, 0.2)', f'rgba({", ".join(value.strip() for value in rgb_values)}, 1)'
    else:
        return hex_color, hex_color