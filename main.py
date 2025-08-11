#!/usr/bin/env python3
"""
SillyVisualizer - Main Entry Point for Docker Container

This module serves as the main entry point for the Docker container,
launching the Flask web application.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import and run the Flask application
from web_application.backend import app

if __name__ == '__main__':
    # Configure for production deployment
    port = int(os.environ.get('PORT', 3000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    print(f"Starting SillyVisualizer on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    # Run the Flask application
    app.run(
        host=host,
        port=port,
        debug=debug
    )
