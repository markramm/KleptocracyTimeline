#!/usr/bin/env python3
"""
Main API server using the app factory pattern
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.app_factory import create_app

def main():
    """Run the API server"""
    # Get configuration from environment
    config_name = os.environ.get('API_CONFIG', 'development')
    
    # Create app
    app = create_app(config_name)
    
    # Get port from configuration
    port = app.config.get('API_PORT', 5000)
    
    # Run server
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config.get('DEBUG', False)
    )


if __name__ == '__main__':
    main()