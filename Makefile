# GPTrans Makefile

.PHONY: help setup dev up down clean test lint format docs

# Default target
help:
	@echo "GPTrans - 智能文档翻译排版系统"
	@echo ""
	@echo "Available commands:"
	@echo "  setup     - Set up development environment"
	@echo "  dev       - Start development servers"
	@echo "  up        - Start production environment with Docker"
	@echo "  down      - Stop all services"
	@echo "  clean     - Clean up containers and volumes"
	@echo "  test      - Run test suite"
	@echo "  lint      - Run code linting"
	@echo "  format    - Format code"
	@echo "  docs      - Generate documentation"
	@echo ""

# Development setup
setup:
	@echo "🔧 Setting up GPTrans development environment..."
	cp .env.example .env
	docker-compose up postgres redis -d
	cd app && pip3 install -r infra/requirements.txt
	cd app/frontend && npm install
	@echo "✅ Setup complete! Run 'make dev' to start development servers"

# Development mode
dev:
	@echo "🚀 Starting development servers..."
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"
	docker-compose up postgres redis -d
	cd app && python3 run_backend.py &
	cd app && python3 run_workers.py &
	cd app/frontend && npm run dev

# Production environment
up:
	@echo "🐳 Starting GPTrans with Docker..."
	docker-compose up -d
	@echo "✅ GPTrans is running!"
	@echo "Frontend: http://localhost:3000"
	@echo "API Docs: http://localhost:8000/docs"

# Stop services
down:
	@echo "🛑 Stopping all services..."
	docker-compose down

# Clean up
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker-compose down -v
	docker system prune -f

# Run tests
test:
	@echo "🧪 Running test suite..."
	cd app && python3 -m pytest tests/ -v --cov=.

# Lint code
lint:
	@echo "🔍 Running linters..."
	cd app && flake8 .
	cd app && mypy backend/ --ignore-missing-imports
	cd app/frontend && npm run lint

# Format code
format:
	@echo "✨ Formatting code..."
	cd app && black .
	cd app && isort .
	cd app/frontend && npm run format

# Generate docs
docs:
	@echo "📚 Generating documentation..."
	mkdir -p docs
	cd scripts && python generate_openapi.py
	@echo "✅ Documentation generated in docs/"

# Database migrations
migrate:
	@echo "📊 Running database migrations..."
	docker-compose exec postgres psql -U gptrans -d gptrans -f /docker-entrypoint-initdb.d/001_initial.sql

# View logs
logs:
	docker-compose logs -f

# Backup data
backup:
	@echo "💾 Creating data backup..."
	docker-compose exec postgres pg_dump -U gptrans gptrans > backup_$(shell date +%Y%m%d_%H%M%S).sql
	tar -czf data_backup_$(shell date +%Y%m%d_%H%M%S).tar.gz data/

# Health check
health:
	@echo "🏥 Checking service health..."
	@curl -s http://localhost:8000/api/health || echo "❌ Backend not responding"
	@curl -s http://localhost:3000 > /dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend not responding"

# Show running services
status:
	@echo "📊 Service status:"
	docker-compose ps