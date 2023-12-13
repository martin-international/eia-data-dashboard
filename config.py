import os

class Config:
    API_KEY = 'YOUR_API_KEY' # Replace with your EIA API Key
    SECRET_KEY = os.environ.get('SECRET_KEY', '#7gjkemu893Uk4_2')
    DEBUG = False
    TESTING = False
    DATABASE_URI = os.environ.get('DATABASE_URI', 'sqlite:///default.db')

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
