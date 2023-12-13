import unittest
from unittest.mock import patch
from main import app

class MainTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        self.app = app.test_client()

    def tearDown(self):
        pass

    @patch('main.Database')
    @patch('main.eia_api')
    def test_index_route(self, mock_eia_api, mock_database):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()