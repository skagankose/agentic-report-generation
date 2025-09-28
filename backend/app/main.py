"""
Main Flask application factory and entry point
"""
import os
import sys
from flask import Flask
from flask_socketio import SocketIO

# Add the open_deep_research module to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'open_deep_research'))

from .core.config import settings
from .api.routes import api_bp, init_routes
from .services.report_service import ReportService


def create_app() -> Flask:
    """Create and configure Flask application"""
    app = Flask(__name__, 
                template_folder='../../frontend/src/templates',
                static_folder='../../frontend/public/static')
    
    # Configure app
    app.config['SECRET_KEY'] = settings.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = settings.MAX_CONTENT_LENGTH
    
    # Initialize SocketIO
    socketio = SocketIO(app, cors_allowed_origins="*")
    
    # Initialize services
    report_service = ReportService(socketio)
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Initialize routes with dependencies
    init_routes(socketio, report_service)
    
    return app, socketio


def main():
    """Main entry point"""
    # Validate configuration
    if not settings.has_search_key:
        print("Warning: TAVILY_API_KEY not set. Search functionality may not work.")
    
    if not settings.has_llm_key:
        print("Warning: No LLM API key set. Report generation will fail.")
    
    # Create app
    app, socketio = create_app()
    
    # Run application
    socketio.run(app, 
                debug=settings.DEBUG, 
                host=settings.HOST, 
                port=settings.PORT)


if __name__ == '__main__':
    main()
