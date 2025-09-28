# Development Guide

## Getting Started

### Prerequisites
- Docker and Docker Compose
- Git
- Text editor/IDE

### Quick Start
```bash
git clone <repo-url>
cd deep-research-report-main
cp .env.example .env
# Edit .env with your API keys
make install
```

## Development Workflow

### Local Development
1. **Environment Setup**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

2. **Start Development Environment**
   ```bash
   make up-build
   ```

3. **View Logs**
   ```bash
   make logs
   ```

4. **Stop Environment**
   ```bash
   make down
   ```

### Code Structure

#### Backend Development
- **Location**: `backend/app/`
- **Entry Point**: `backend/app/main.py`
- **Configuration**: `backend/app/core/config.py`

#### Adding New API Endpoints
1. Create route in `backend/app/api/routes.py`
2. Add business logic in `backend/app/services/`
3. Create models if needed in `backend/app/models/`

#### Adding New Services
1. Create service class in `backend/app/services/`
2. Import and initialize in `backend/app/main.py`
3. Use dependency injection pattern

### Frontend Development
- **Static Files**: `frontend/public/static/`
- **Templates**: `frontend/src/templates/`
- **Nginx Config**: `docker/nginx.conf`

### Testing

#### Running Tests
```bash
# Backend tests
docker exec -it deep-research-backend python -m pytest

# Or run specific test file
docker exec -it deep-research-backend python -m pytest tests/test_specific.py
```

#### Writing Tests
- Place tests in `backend/tests/`
- Follow naming convention: `test_*.py`
- Use pytest fixtures for setup

### Debugging

#### Backend Debugging
1. **View Application Logs**
   ```bash
   docker logs deep-research-backend -f
   ```

2. **Access Container Shell**
   ```bash
   docker exec -it deep-research-backend bash
   ```

3. **Debug Mode**
   - Set `FLASK_ENV=development` in `.env`
   - Restart containers

#### Frontend Debugging
1. **Nginx Logs**
   ```bash
   docker logs deep-research-frontend -f
   ```

2. **Static File Issues**
   - Check `docker/nginx.conf`
   - Verify file paths in `docker/Dockerfile.frontend`

### Common Issues

#### Port Conflicts
- Change port in `docker/docker-compose.yml`
- Update health checks accordingly

#### API Key Issues
- Verify `.env` file exists and has correct keys
- Check environment variable names match `backend/app/core/config.py`

#### Import Errors
- Ensure all `__init__.py` files exist
- Check Python path configuration in Dockerfile

### Performance Optimization

#### Backend
- Use async/await for I/O operations
- Implement caching for repeated requests
- Optimize database queries

#### Frontend
- Minimize CSS/JS files
- Use CDN for external libraries
- Implement proper caching headers in Nginx

### Deployment

#### Production Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong secret keys
- [ ] Configure proper logging
- [ ] Set up monitoring
- [ ] Configure backup strategy

#### Environment Variables
```bash
# Required
ANTHROPIC_API_KEY=your_key
TAVILY_API_KEY=your_key

# Optional
OPENAI_API_KEY=your_key
FLASK_SECRET_KEY=random_secret
```
