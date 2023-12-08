# EIA Data Visualization Tool

## Objective

The EIA Data Visualization Tool is a web application designed to provide dynamic, interactive visual representations of energy data. By leveraging data from the U.S. Energy Information Administration (EIA), it offers valuable insights into energy consumption, production, and trends.

## Intended Audience

This tool is designed for commodity investors seeking to track energy market trends, climate scientists examining environmental impacts, and demand forecasters predicting future energy requirements.

## Frameworks and Technologies

Constructed with a Python Flask backend, this application utilizes SQLite for database operations, Plotly for interactive graphing, and Pandas alongside NumPy for data manipulation and computation. Statistical analysis is performed using PMDARIMA and Statsmodels for ARIMA modeling, optimized by concurrent futures for enhanced performance.

## Application Workflow

The workflow of the application is streamlined for efficiency:

1. **Data Acquisition**: Data is fetched from the EIA API, focusing on the user-defined periods to optimize load times.
2. **Data Storage**: Utilizes SQLite to manage and query energy data efficiently.
3. **Data Processing**: Employs Pandas and NumPy for data transformation, preparing it for analysis.
4. **Statistical Analysis**: Performs ARIMA modeling for precise time series forecasting.
5. **Visualization**: Generates interactive visualizations using Plotly, offering a comprehensive data exploration experience.
6. **User Interaction**: Provides an intuitive interface for users to interact with the data visualizations effectively.

![screenshot of index.html](https://github.com/martin-international/eia-data-dashboard/blob/main/readme/index.png)

![screenshot of select_states.html](https://github.com/martin-international/eia-data-dashboard/blob/main/readme/select_states.png)

![screenshot of select_features.html](https://github.com/martin-international/eia-data-dashboard/blob/main/readme/select_features.png)

![gif of dashboard.html](https://github.com/martin-international/eia-data-dashboard/blob/main/readme/dashboard.gif)

## Functionalities

The tool includes functionalities such as:

- **Statistical Range Projections**: Projects potential future trends using historical data.
- **ARIMA Projections**: Employs ARIMA models for time series forecasting.
- **Interactive Graphs**: Enables users to delve into data with interactive, customizable graphs.
- **Heatmaps**: Visualizes geographic data representations for regional comparison and analysis.
- **Data Normalization**: Ensures comparability across different scales of data.
- **Accessibility**: Adopts a color-blind-safe palette for inclusivity.

## App Limitations

While the application is designed to be comprehensive and user-friendly, it operates within the following constraints:

- **Data Quality**: The accuracy of the visualizations and forecasts is contingent on the EIA's data integrity.
- **Performance Scalability**: Optimized for standard datasets, additional optimization may be required for larger datasets.
- **Processing Time Variability**: Data processing times may differ based on the dataset size and system specifications.

## Extendability and Optimization

- **Modular Design**: Simplifies the integration of additional datasets with minimal adjustments.
- **Performance**: Utilizes parallel processing and smart data fetching to enhance user experience and resource efficiency.

## Quick Start

To set up the EIA Data Visualization Tool locally:

1. **Clone the Repository**:
   ```sh
   git clone https://github.com/martin-international/eia-data-dashboard.git
   cd eia-data-visualization
   ```

2. **Set Up the Environment**:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts ctivate`
   pip install -r requirements.txt
   ```

3. **Add your EIA API Key**
   Replace YOUR_API_KEY in config.py with your own EIA API key.
   An API key may be acquired for free at: https://www.eia.gov/opendata/register.php

4. **Launch the Application**:
   ```sh
   python main.py
   ```
   A browser window should automatically open to `http://127.0.0.1:5000/`. If it does not, you may also manually navigate to this address.

---