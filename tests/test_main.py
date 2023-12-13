import unittest
from unittest.mock import patch, MagicMock
from flask import session, template_rendered
from main import app

class MainTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

    @patch('main.eia_api')
    def test_fetch_data_route(self, mock_eia_api):
        with self.app as client:
            response = client.post('/fetch_data', data={'start_year': '2020', 'end_year': '2021'})
            self.assertEqual(response.status_code, 302)  # Assuming it redirects after successful post
            with client.session_transaction() as sess:
                self.assertIn('date_range', sess)  # Checks if 'date_range' is in session

    @patch('main.Database')
    def test_select_states_route(self, mock_database):
        response = self.app.get('/select_states')
        self.assertEqual(response.status_code, 200)

    @patch('main.Database')
    def test_select_features_route(self, mock_database):
        response = self.app.get('/select_features')
        self.assertEqual(response.status_code, 200)

    @patch('main.Database')
    def test_get_data_for_graphs_route(self, mock_database):
        response = self.app.get('/get_data_for_graphs')
        self.assertEqual(response.status_code, 200)

    @patch('main.create_combined_graph')
    @patch('main.Database')
    def test_create_graphs_route(self, mock_database, mock_create_combined_graph):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['selected_states'] = ['State1', 'State2']
                sess['date_range'] = ('2020-01-01', '2020-12-31')
                sess['units_fields'] = {}
            response = client.post('/create_graphs', data={'features': ['Feature1', 'Feature2']})
            self.assertEqual(response.status_code, 200)

    @patch('main.create_graph')
    @patch('main.Database')
    def test_dashboard_route(self, mock_database, mock_create_graph):
        with self.app as client:
            with client.session_transaction() as sess:
                sess['selected_states'] = ['State1', 'State2']
                sess['selected_elements'] = ['Element1', 'Element2']
                sess['date_range'] = ('2020-01-01', '2020-12-31')
                sess['units_fields'] = {}
            response = client.get('/dashboard')
            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
