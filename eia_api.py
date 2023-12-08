import requests
import json
from database import Database
from datetime import datetime
from flask import session

class EIA_API:
    def __init__(self, api_key, db_path='eia_data.db'):
        self.api_key = api_key
        self.db_path = db_path
        # Base URL for EIA API requests
        self.base_url = 'https://api.eia.gov/v2/electricity/state-electricity-profiles/source-disposition/data/?frequency=annual&data%5B0%5D=combined-heat-and-pwr-comm&data%5B1%5D=combined-heat-and-pwr-elect&data%5B2%5D=combined-heat-and-pwr-indust&data%5B3%5D=direct-use&data%5B4%5D=elect-pwr-sector-gen-subtotal&data%5B5%5D=electric-utilities&data%5B6%5D=energy-only-providers&data%5B7%5D=estimated-losses&data%5B8%5D=facility-direct&data%5B9%5D=full-service-providers&data%5B10%5D=independent-power-producers&data%5B11%5D=indust-and-comm-gen-subtotal&data%5B12%5D=net-trade-index&data%5B13%5D=total-elect-indust&data%5B14%5D=total-international-exports&data%5B15%5D=total-international-imports&data%5B16%5D=total-net-generation&data%5B17%5D=total-supply&sort%5B0%5D%5Bcolumn%5D=period&sort%5B0%5D%5Bdirection%5D=desc&offset=0&length=5000'

    def fetch_and_store_data(self, start_date=None, end_date=None, fetch_sample=False):
        """Fetches data from EIA API and stores it in the database."""
        if fetch_sample:
            self._fetch_sample_data()
        else:
            self._fetch_full_data(start_date, end_date)

    def _fetch_sample_data(self):
        """Fetches sample data to initialize the database."""
        current_year = datetime.now().year
        while current_year >= 2000:
            formatted_date = f"{current_year}-01-01"
            sample_url = f"{self.base_url}&start={formatted_date}&end={formatted_date}&api_key={self.api_key}"
            response = self.make_paginated_request(sample_url, 0, 1)
            response_json = response.json()

            if self._is_valid_data(response_json):
                sample_data = response_json['response']['data'][0]
                self.init_db(sample_data)
                break
            else:
                current_year -= 1

    def _fetch_full_data(self, start_date, end_date):
        """Fetches full data for the given date range."""
        full_data_url = f"{self.base_url}&start={start_date}&end={end_date}&api_key={self.api_key}"
        offset = 0
        page_size = 5000
        total_rows = None
        units_fields = {}
        
        while total_rows is None or offset < total_rows:
            response = self.make_paginated_request(full_data_url, offset, page_size)
            data = response.json()
            if 'response' in data and 'data' in data['response']:
                total_rows = total_rows or data['response']['total']
                self.store_data_batch(data['response']['data'])
                for item in data['response']['data']:
                        for key, value in item.items():
                            if key.endswith('-units'):
                                unit_key = key[:-6].replace('-', '_')  # Remove '_units' suffix and replace hyphens with underscores
                                units_fields[unit_key] = value
            offset += page_size
            session['units_fields'] = units_fields
        

    def make_paginated_request(self, url, offset, page_size):
        """Makes a paginated request to the EIA API."""
        params = {'offset': offset, 'length': page_size}
        response = requests.get(url, params=params)
        return response

    def init_db(self, sample_data):
        """Initializes the database with sample data structure."""
        columns = ', '.join([f"{key.replace('-', '_')} TEXT" for key in sample_data.keys()])
        with Database(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f'CREATE TABLE IF NOT EXISTS eia_data ({columns})')

    def store_data_batch(self, data_batch):
        """Stores a batch of data in the database."""
        with Database(self.db_path) as conn:
            for data_item in data_batch:
                self._store_single_data_item(conn, data_item)
                
    def calculate_increase_for_feature(self, feature, start_date, end_date):
        """
        Calculate the increase for a given feature between two dates.
        """
        with Database(self.db_path) as conn:
            cursor = conn.cursor()
            query = f"""
                SELECT state, SUM(\"{feature}\") AS total
                FROM eia_data
                WHERE period BETWEEN ? AND ?
                GROUP BY state
            """
            cursor.execute(query, (start_date, end_date))
            data = cursor.fetchall()

        # Assume 'data' is a list of tuples in the form: [(state, total), ...]
        # Convert to a dictionary: {state: total, ...}
        #return {state: total for state, total in data if total is not None}
        increase_data = {state: total for state, total in data if total is not None}
        
        return increase_data

    def _store_single_data_item(self, conn, data_item):
        """Stores a single data item in the database."""
        cursor = conn.cursor()
        columns = ', '.join([key.replace('-', '_') for key in data_item.keys()])
        placeholders = ', '.join(['?'] * len(data_item))
        values = [data_item.get(key) for key in data_item.keys()]
        sql = f'INSERT INTO eia_data ({columns}) VALUES ({placeholders})'
        cursor.execute(sql, values)
        conn.commit()

    @staticmethod
    def _is_valid_data(response_json):
        """Checks if the response JSON contains valid data."""
        return ('response' in response_json and 
                'data' in response_json['response'] and 
                response_json['response']['data'])
    
    

