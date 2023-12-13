import unittest
import utilities
from database import Database

class TestUtilities(unittest.TestCase):

    def test_normalize_data(self):
        data = {'a': 1, 'b': 2, 'c': 3}
        expected = {'a': 0.0, 'b': 0.5, 'c': 1.0}
        result = utilities.normalize_data(data)
        self.assertEqual(result, expected)
        
        data_same = {'a': 1, 'b': 1, 'c': 1}
        expected_same = {'a': 0.5, 'b': 0.5, 'c': 0.5}
        result_same = utilities.normalize_data(data_same)
        self.assertEqual(result_same, expected_same)
    
    def test_arima_forecast(self):
        historical_values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        num_predictions = 5
        result = utilities.arima_forecast(historical_values, num_predictions)
        self.assertEqual(len(result), num_predictions)
    
    def test_hex_to_rgba(self):
        hex_color = "#FF5733"
        expected_rgba = ('rgba(255, 87, 51, 0.2)', 'rgba(255, 87, 51, 1)')
        result = utilities.hex_to_rgba(hex_color)
        self.assertEqual(result, expected_rgba)

if __name__ == '__main__':
    unittest.main()
