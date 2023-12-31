import unittest
from unittest.mock import patch, MagicMock
from eia_api import EIA_API
from flask import Flask

class TestEIAAPI(unittest.TestCase):

    @patch('eia_api.requests.get')
    @patch('eia_api.EIA_API.store_data_batch')
    def test_fetch_and_store_data(self, mock_store_data_batch, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': {
                'data': [{'period': 'dummy_data'}],  
                'total': 1
            }
        }
        mock_get.return_value = mock_response
        
        app = Flask(__name__)
        app.secret_key = 'test_secret_key'

        with app.test_request_context():
            api = EIA_API('dummy_api_key')
            api.fetch_and_store_data()

        mock_get.assert_called_once()
        mock_store_data_batch.assert_called()


    @patch('eia_api.Database')
    def test_store_data_batch(self, mock_database):
        mock_conn = MagicMock()
        mock_database.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        data_batch = [{'data': 'value1'}, {'data': 'value2'}]
        api = EIA_API('dummy_api_key')
        api.store_data_batch(data_batch)

        mock_database.assert_called_once()
        assert mock_cursor.execute.call_count == len(data_batch)
        expected_query = "INSERT INTO eia_data (data) VALUES (?)"
        mock_cursor.execute.assert_called_with(expected_query, ['value2'])

    @patch('eia_api.Database')
    def test_calculate_increase_for_feature(self, mock_database):
        mock_conn = MagicMock()
        mock_database.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchall.return_value = [('State1', 100), ('State2', 200)]

        api = EIA_API('dummy_api_key')
        result = api.calculate_increase_for_feature('feature_name', '2000-01-01', '2020-01-01')

        mock_cursor.execute.assert_called_once()
        self.assertEqual(result, {'State1': 100, 'State2': 200})

    @patch('eia_api.Database')
    def test_store_single_data_item_within_store_data_batch(self, mock_database):
        mock_conn = MagicMock()
        mock_database.return_value.__enter__.return_value = mock_conn
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor

        data_batch = [{'your_column_name': 'value1'}, {'your_column_name': 'value2'}]
        api = EIA_API('dummy_api_key')
        api.store_data_batch(data_batch)

        assert mock_cursor.execute.call_count == len(data_batch)
        expected_query = "INSERT INTO eia_data (your_column_name) VALUES (?)"
        mock_cursor.execute.assert_called_with(expected_query, ['value2'])

    def test_is_valid_data(self):
        valid_response = {
            'response': {
                'data': [1, 2, 3]
            }
        }
        invalid_response = {
            'response': {
                'data': None
            }
        }

        self.assertTrue(EIA_API._is_valid_data(valid_response))
        self.assertFalse(EIA_API._is_valid_data(invalid_response))

if __name__ == '__main__':
    unittest.main()
