"""
Configuration settings for 5G Network Slice Simulator
Loads environment variables from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration"""
    
    # MySQL Database Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "5g_simulator")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    
    # Build database URL for SQLAlchemy
    DATABASE_URL = f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    
    # Backend Configuration
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", 8000))
    
    # Slice Services Configuration (ports they run on)
    SLICE_SERVICES = {
        "embb": {"host": "localhost", "port": 8101},
        "urllc": {"host": "localhost", "port": 8102},
        "mmtc": {"host": "localhost", "port": 8103}
    }
    
    # Scheduler Service Configuration
    SCHEDULER_SERVICE = {"host": "localhost", "port": 8001}
    
    # Application Settings
    APP_NAME = "5G Network Slice Simulator"
    APP_VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False") == "True"
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # Simulation Settings
    MAX_TRAFFIC_VOLUME = 1000000
    MIN_TRAFFIC_VOLUME = 100
    MAX_DURATION = 3600  # seconds
    MIN_DURATION = 10    # seconds
    
    # Valid traffic patterns
    VALID_PATTERNS = ["constant", "linear_increase", "burst", "wave"]
    
    # CORS Settings
    CORS_ORIGINS = ["*"]
    CORS_CREDENTIALS = True
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = "INFO"

# Select config based on environment
ENV = os.getenv("ENVIRONMENT", "development")
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()