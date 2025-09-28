# Project Architecture

## Overview

This is a containerized AI-powered feasibility report generator built with Flask backend and Nginx frontend proxy.

## Architecture Components

### Backend (`/backend`)
- **Framework**: Flask with Flask-SocketIO for real-time communication
- **Structure**: Modular architecture with separation of concerns
- **AI Engine**: Integration with open_deep_research for report generation
- **Export**: Support for Word (.docx) and Markdown (.md) formats

### Frontend (`/frontend`)
- **Static Files**: CSS, JavaScript, and assets served by Nginx
- **Templates**: Jinja2 templates for server-side rendering
- **Real-time**: WebSocket integration for progress updates

### Docker (`/docker`)
- **Multi-container**: Separate containers for backend and frontend
- **Networking**: Internal Docker network for service communication
- **Volumes**: Persistent storage for temporary files and data

## Data Flow

```
User Request → Nginx → Flask Backend → AI Engine → Response
     ↑                                      ↓
WebSocket ← Progress Updates ← Report Generation
```

## Key Features

1. **Modular Backend Structure**
   - `api/`: REST endpoints and WebSocket handlers
   - `core/`: Configuration and application settings
   - `models/`: Data structures and schemas
   - `services/`: Business logic and AI integration
   - `utils/`: Helper functions and utilities

2. **Real-time Progress Tracking**
   - WebSocket-based progress updates
   - Session management for concurrent users
   - Step-by-step generation feedback

3. **Document Export**
   - Multiple format support (Word, Markdown)
   - Professional styling and formatting
   - Automatic filename generation

4. **Containerized Deployment**
   - Production-ready Docker setup
   - Nginx reverse proxy and static file serving
   - Health checks and restart policies

## Development Guidelines

### Adding New Features
1. Create models in `backend/app/models/`
2. Implement business logic in `backend/app/services/`
3. Add API endpoints in `backend/app/api/`
4. Update tests in `backend/tests/`

### Configuration
- Environment variables in `.env`
- Application settings in `backend/app/core/config.py`
- Docker configuration in `docker/` directory

### Testing
- Unit tests for services and utilities
- Integration tests for API endpoints
- Docker health checks for deployment validation
