import unittest
from config import Config, DevelopmentConfig, TestingConfig

class ConfigMixin:
    def test_common_attributes(self):
        self.assertEqual(self.config.API_KEY, 'YOUR_API_KEY')
        self.assertEqual(self.config.SECRET_KEY, '#7gjkemu893Uk4_2')
        self.assertEqual(self.config.DATABASE_URI, 'sqlite:///default.db')

class TestDefaultConfig(ConfigMixin, unittest.TestCase):
    def setUp(self):
        self.config = Config

    def test_debug_and_testing(self):
        self.assertFalse(self.config.DEBUG)
        self.assertFalse(self.config.TESTING)

class TestDevelopmentConfig(ConfigMixin, unittest.TestCase):
    def setUp(self):
        self.config = DevelopmentConfig

    def test_debug(self):
        self.assertTrue(self.config.DEBUG)

class TestTestingConfig(ConfigMixin, unittest.TestCase):
    def setUp(self):
        self.config = TestingConfig

    def test_testing(self):
        self.assertTrue(self.config.TESTING)

if __name__ == '__main__':
    unittest.main()
