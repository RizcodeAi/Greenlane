up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

test-backend:
	cd backend && pytest

test-frontend:
	cd frontend && npm test

logs:
	docker-compose logs -f

lint-backend:
	cd backend && ruff check .

lint-frontend:
	cd frontend && npm run lint