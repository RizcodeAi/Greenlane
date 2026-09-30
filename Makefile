# GreenLane Maritime Platform — Makefile
#
# Targets use `docker compose` (Compose V2 plugin).
# Make requires Docker to be running for most targets.
#
# Usage:
#   make <target>
#
# All paths are relative to the project root.

# Colors for output
RED     := $(shell tput setaf 1 2>/dev/null || echo "")
GREEN   := $(shell tput setaf 2 2>/dev/null || echo "")
YELLOW  := $(shell tput setaf 3 2>/dev/null || echo "")
RESET   := $(shell tput sgr0 2>/dev/null || echo "")

# Detect if Docker is running
DOCKER_RUNNING := $(shell docker info --format '{{.ServerVersion}}' 2>/dev/null)

ifeq ($(DOCKER_RUNNING),)
	$(error Docker is not running. Please start Docker and try again.)
endif

.PHONY: all up down build logs test test-frontend lint lint-frontend verify migrate certs clean backup restore shell-backend shell-mongo help

# --- Default target ---
all: build up

# --- Service Management ---

## Start all services in detached mode
up:
	@echo "$(GREEN)Starting GreenLane services...$(RESET)"
	docker compose up -d
	@echo "$(GREEN)Services started. Run 'make ps' to check status.$(RESET)"

## Stop all services
down:
	@echo "$(YELLOW)Stopping GreenLane services...$(RESET)"
	docker compose down
	@echo "$(GREEN)Services stopped.$(RESET)"

## Build all Docker images
build:
	@echo "$(GREEN)Building Docker images...$(RESET)"
	docker compose build
	@echo "$(GREEN)Build complete.$(RESET)"

## Show service logs in real-time
logs:
	@echo "$(YELLOW)Streaming service logs (press Ctrl+C to stop)...$(RESET)"
	docker compose logs -f --tail 100

## Show running services and their status
ps:
	docker compose ps

# --- Testing ---

## Run backend tests (pytest)
test:
	@echo "$(GREEN)Running backend tests...$(RESET)"
	cd backend && pytest -v
	@echo "$(GREEN)Backend tests complete.$(RESET)"

## Run frontend tests (vitest)
test-frontend:
	@echo "$(GREEN)Running frontend tests...$(RESET)"
	cd frontend && npm test -- --run
	@echo "$(GREEN)Frontend tests complete.$(RESET)"

# --- Linting ---

## Run linters on backend (ruff) and frontend (eslint)
lint: lint-backend lint-frontend

## Run flake8 and black on backend Python code
lint-backend:
	@echo "$(GREEN)Running backend linter...$(RESET)"
	cd backend && ruff check .
	@echo "$(GREEN)Backend lint complete.$(RESET)"

## Run ESLint on frontend TypeScript code
lint-frontend:
	@echo "$(GREEN)Running frontend linter...$(RESET)"
	cd frontend && npm run lint
	@echo "$(GREEN)Frontend lint complete.$(RESET)"

# --- Verification ---

## Run the verification script (PowerShell)
verify:
	@echo "$(YELLOW)Running verification script...$(RESET)"
	powershell -ExecutionPolicy Bypass -File verify.ps1
	@echo "$(GREEN)Verification complete.$(RESET)"

# --- Database ---

## Initialize database and create indexes
migrate:
	@echo "$(GREEN)Initializing database and indexes...$(RESET)"
	docker compose exec backend python -c "import asyncio; from app.core.database import init_db_indexes, db; asyncio.run(init_db_indexes(db))"
	@echo "$(GREEN)Database initialization complete.$(RESET)"

## Backup MongoDB to a tar archive
backup:
	@echo "$(GREEN)Backing up MongoDB...$(RESET)"
	docker compose exec mongo mongodump --out /backup/$$(date +%Y%m%d_%H%M%S)
	@echo "$(GREEN)MongoDB backup complete.$(RESET)"

## Restore MongoDB from a backup archive
restore:
	@echo "$(YELLOW)Restoring MongoDB from backup...$(RESET)"
	docker compose exec mongo mongorestore /backup/latest
	@echo "$(GREEN)MongoDB restore complete.$(RESET)"

# --- Certificates ---

## Generate TLS certificates using generate_certs.sh
certs:
	@echo "$(GREEN)Generating TLS certificates...$(RESET)"
	./generate_certs.sh generate
	@echo "$(GREEN)Certificates generated in certs/$(RESET)"

# --- Cleanup ---

## Remove containers, networks, and volumes (destructive)
clean:
	@echo "$(RED)Removing containers, networks, and volumes...$(RESET)"
	docker compose down -v --remove-orphans
	@echo "$(GREEN)Cleanup complete.$(RESET)"

# --- Shell Access ---

## Open a shell in the backend container
shell-backend:
	docker compose exec backend sh

## Open a shell in the MongoDB container
shell-mongo:
	docker compose exec mongo mongosh greenlane_db

# --- Help ---

## Show this help message
help:
	@echo "$(YELLOW)GreenLane Maritime Platform — Makefile$(RESET)"
	@echo ""
	@echo "$(GREEN)Available targets:$(RESET)"
	@echo ""
	@echo "  Service Management:"
	@echo "    make up              Start all services"
	@echo "    make down            Stop all services"
	@echo "    make build           Build all Docker images"
	@echo "    make logs            Stream service logs"
	@echo "    make ps              Show running services"
	@echo ""
	@echo "  Testing:"
	@echo "    make test            Run backend tests (pytest)"
	@echo "    make test-frontend   Run frontend tests (vitest)"
	@echo ""
	@echo "  Linting:"
	@echo "    make lint            Run all linters"
	@echo "    make lint-backend    Run backend linter (ruff)"
	@echo "    make lint-frontend   Run frontend linter (eslint)"
	@echo ""
	@echo "  Verification:"
	@echo "    make verify          Run verify.ps1"
	@echo ""
	@echo "  Database:"
	@echo "    make migrate         Initialize DB indexes"
	@echo "    make backup          Backup MongoDB"
	@echo "    make restore         Restore MongoDB"
	@echo ""
	@echo "  Certificates:"
	@echo "    make certs           Generate TLS certificates"
	@echo ""
	@echo "  Cleanup:"
	@echo "    make clean           Remove containers, networks, volumes"
	@echo ""
	@echo "  Shell Access:"
	@echo "    make shell-backend   Open shell in backend container"
	@echo "    make shell-mongo     Open shell in MongoDB container"
	@echo ""
	@echo "  Other:"
	@echo "    make help            Show this help message"
	@echo ""
	@echo "$(YELLOW)Note: Docker must be running for most targets.$(RESET)"
