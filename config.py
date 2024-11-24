import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_very_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Aevo API configuration
    AEVO_SIGNING_KEY = os.environ.get('AEVO_SIGNING_KEY')
    WALLET_ADDRESS = os.environ.get('WALLET_ADDRESS')
    AEVO_API_KEY = os.environ.get('AEVO_API_KEY')
    AEVO_API_SECRET = os.environ.get('AEVO_API_SECRET')
    ENV = os.environ.get('ENV', 'mainnet')
    
    # Celery configuration
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')