"""
Flask application factory with dependency injection for better testability
"""

from flask import Flask
from flask_cors import CORS
from typing import Optional, Dict, Any
import os
from pathlib import Path


class Config:
    """Base configuration"""
    TESTING = False
    DEBUG = False
    DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///research.db')
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    TIMELINE_DIR = Path('timeline_data/events')
    API_PORT = int(os.environ.get('API_PORT', 5000))
    CORS_ORIGINS = '*'


class TestConfig(Config):
    """Test configuration"""
    TESTING = True
    DATABASE_URL = 'sqlite:///:memory:'
    TIMELINE_DIR = Path('/tmp/test_timeline')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'https://yourdomain.com')


def create_app(config_name: str = 'development', 
               services: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create Flask app with dependency injection
    
    Args:
        config_name: Configuration to use ('testing', 'development', 'production')
        services: Optional dictionary of services to inject
    
    Returns:
        Configured Flask application
    """
    
    # Select configuration
    configs = {
        'testing': TestConfig,
        'development': DevelopmentConfig,
        'production': ProductionConfig
    }
    config_class = configs.get(config_name, DevelopmentConfig)
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize CORS
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Inject services
    if services:
        app.services = services
    else:
        # Default services
        from api.services import (
            EventService,
            ValidationService,
            FileService,
            DatabaseService
        )
        
        app.services = {
            'event_service': EventService(app.config['TIMELINE_DIR']),
            'validation_service': ValidationService(),
            'file_service': FileService(),
            'database_service': DatabaseService(app.config['DATABASE_URL'])
        }
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    return app


def register_blueprints(app: Flask):
    """Register application blueprints"""
    
    from api.routes.events import events_bp
    from api.routes.validation import validation_bp
    from api.routes.monitoring import monitoring_bp
    
    app.register_blueprint(events_bp, url_prefix='/api/events')
    app.register_blueprint(validation_bp, url_prefix='/api/validation')
    app.register_blueprint(monitoring_bp, url_prefix='/api/monitoring')


def register_error_handlers(app: Flask):
    """Register error handlers"""
    
    @app.errorhandler(404)
    def not_found(error):
        return {'error': 'Resource not found'}, 404
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'error': 'Bad request'}, 400
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return {'error': 'Internal server error'}, 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return {'error': 'An unexpected error occurred'}, 500