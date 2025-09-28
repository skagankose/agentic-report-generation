# Agentic Report Generation

This web application generates comprehensive feasibility reports using large language models and deep research tools. It creates detailed reports covering technical analysis, market analysis, cost analysis, financial analysis, and risk assessment for any given topic.

## Features

- AI-powered report generation
- Real-time progress tracking
- Export to Word (.docx) and Markdown (.md) formats
- Modern, responsive web interface
- WebSocket-based progress updates

## Requirements

- Python 3.8+
- Flask
- Flask-SocketIO
- pypandoc
- python-docx
- Anthropic API key or OpenAI API key
- Tavily API key (for search functionality)

## Project Structure

```
deep-research-report-main/
├── backend/                    # Backend Flask application
│   ├── app/                   # Main application code
│   │   ├── api/              # API routes and endpoints
│   │   ├── core/             # Core configuration and settings
│   │   ├── models/           # Data models and schemas
│   │   ├── services/         # Business logic services
│   │   ├── utils/            # Utility functions
│   │   └── main.py           # Application entry point
│   ├── config/               # Configuration files
│   ├── requirements/         # Python dependencies
│   └── tests/                # Backend tests
├── frontend/                  # Frontend static files
│   ├── public/               # Static assets (CSS, JS, images)
│   └── src/                  # Source templates and components
├── docker/                   # Docker configuration
│   ├── Dockerfile.backend    # Backend container definition
│   ├── Dockerfile.frontend   # Frontend container definition
│   └── nginx.conf           # Nginx configuration
├── docs/                     # Documentation and project notes
├── scripts/                  # Build and deployment scripts
├── docker-compose.yml        # Multi-container orchestration
└── open_deep_research/       # AI report generation engine
```

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd deep-research-report-main
```

2. Create environment file:
```bash
cp .env.example .env
```

3. Edit the `.env` file and add your API keys:
```bash
ANTHROPIC_API_KEY=your_anthropic_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

4. Build and run with Docker Compose:
```bash
docker-compose up --build
```

Or use the convenient Makefile:
```bash
make install  # Setup and run everything
```

The application will be available at `http://localhost`

### Management Commands

```bash
# Using Makefile (recommended)
make up-build     # Build and start containers
make down         # Stop containers
make logs         # View logs
make status       # Show container status
make clean        # Clean up everything

# Using Docker Compose directly
docker-compose up -d --build
docker-compose down
docker-compose logs -f
```

## Docker Architecture

The application is containerized using a multi-container setup:

- **Backend Container**: Flask application with all Python dependencies
- **Frontend Container**: Nginx server serving static files and proxying requests to backend
- **Network**: Both containers communicate through a Docker network
- **Volumes**: Temporary files and application data are persisted using Docker volumes

### Container Management

View running containers:
```bash
docker-compose ps
```

View logs:
```bash
docker-compose logs -f
```

Rebuild containers:
```bash
docker-compose build --no-cache
```

## Usage

1. Enter your topic in the input form
2. Click "Generate Report"
3. Monitor real-time progress
4. View or download the report in your preferred format

## License

This project is private and proprietary. All rights reserved. 
