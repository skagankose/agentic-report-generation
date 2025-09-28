.PHONY: build up down logs clean restart

# Build and start containers
build:
	docker-compose build --no-cache

# Start containers
up:
	docker-compose up -d

# Start containers with build
up-build:
	docker-compose up -d --build

# Stop containers
down:
	docker-compose down

# View logs
logs:
	docker-compose logs -f

# Clean up containers, networks, and volumes
clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Restart containers
restart: down up

# Show container status
status:
	docker-compose ps

# Setup environment file
setup:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your API keys."; \
	else \
		echo ".env file already exists."; \
	fi

# Full setup and run
install: setup up-build

help:
	@echo "Available commands:"
	@echo "  make setup      - Create .env file from template"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start containers"
	@echo "  make up-build   - Build and start containers"
	@echo "  make down       - Stop containers"
	@echo "  make logs       - View container logs"
	@echo "  make status     - Show container status"
	@echo "  make restart    - Restart containers"
	@echo "  make clean      - Clean up containers and volumes"
	@echo "  make install    - Full setup and run"
