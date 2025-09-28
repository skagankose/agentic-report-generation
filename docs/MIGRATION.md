# Migration Guide

## Project Restructure

The project has been reorganized from a monolithic structure to a professional, modular architecture.

### What Changed

#### Before (Monolithic)
```
├── app.py                    # Everything in one file
├── static/                   # Mixed with root
├── templates/               # Mixed with root
├── requirements.txt         # Single requirements file
├── Dockerfile.backend       # In root
├── Dockerfile.frontend      # In root
├── docker-compose.yml       # In root
└── open_deep_research/      # AI engine
```

#### After (Modular)
```
├── backend/                 # Organized backend
│   ├── app/
│   │   ├── api/            # Routes separated
│   │   ├── core/           # Configuration
│   │   ├── models/         # Data models
│   │   ├── services/       # Business logic
│   │   ├── utils/          # Utilities
│   │   └── main.py         # Clean entry point
│   └── requirements/       # Dependencies
├── frontend/               # Frontend assets
│   ├── public/static/      # Static files
│   └── src/templates/      # Templates
├── docker/                 # Docker configs
├── docs/                   # Documentation
└── scripts/                # Build scripts
```

### Benefits of New Structure

1. **Separation of Concerns**
   - API routes isolated from business logic
   - Configuration centralized
   - Utilities organized by function

2. **Maintainability**
   - Easier to find and modify code
   - Clear module boundaries
   - Better testing structure

3. **Scalability**
   - Easy to add new features
   - Modular components
   - Professional architecture

4. **Development Experience**
   - Better IDE support
   - Clearer import paths
   - Organized documentation

### Key Improvements

#### Code Organization
- **Modular Backend**: Separated into logical modules
- **Clean Architecture**: Following Flask best practices
- **Type Hints**: Better code documentation and IDE support
- **Configuration Management**: Centralized settings

#### Docker Improvements
- **Organized Structure**: Docker files in dedicated directory
- **Better Paths**: Cleaner build contexts
- **Professional Setup**: Production-ready configuration

#### Documentation
- **Architecture Guide**: Clear system overview
- **Development Guide**: Step-by-step instructions
- **Migration Notes**: This document

### Running the New Structure

#### Quick Start
```bash
# Old way (no longer works)
python app.py

# New way
make install
# or
cd docker && docker-compose up --build
```

#### Development
```bash
# View logs
make logs

# Stop containers
make down

# Clean rebuild
make clean && make up-build
```

### File Mapping

| Old Location | New Location |
|-------------|-------------|
| `app.py` | `backend/app/main.py` + modules |
| `static/` | `frontend/public/static/` |
| `templates/` | `frontend/src/templates/` |
| `requirements.txt` | `backend/requirements/requirements.txt` |
| `Dockerfile.*` | `docker/Dockerfile.*` |
| `docker-compose.yml` | `docker/docker-compose.yml` |

### Breaking Changes

1. **Entry Point**: Changed from `app.py` to `backend/app/main.py`
2. **Docker Commands**: Must run from `docker/` directory or use Makefile
3. **Import Paths**: Internal imports updated for new structure
4. **Configuration**: Now centralized in `backend/app/core/config.py`

### Migration Steps for Developers

1. **Update Local Environment**
   ```bash
   git pull
   make clean  # Clean old containers
   make install  # Setup new structure
   ```

2. **Update IDE Settings**
   - Set Python path to `backend/`
   - Update run configurations
   - Configure linting paths

3. **Update Scripts**
   - Change Docker commands to use new paths
   - Update any deployment scripts
   - Modify CI/CD pipelines if applicable
