.PHONY: install run migrate makemigrations seed test lint docker clean

# Install python requirements locally
install:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# Start FastAPI and React dev servers locally
run:
	@echo "Starting backend and frontend locally..."
	# Starts backend in background, then starts frontend
	cd backend && uvicorn app.main:app --reload --port 8000 &
	cd frontend && npm run dev

# Run Alembic migrations
migrate:
	cd backend && alembic upgrade head

# Autogenerate new Alembic migrations
makemigrations:
	@read -p "Enter migration message: " msg; \
	cd backend && alembic revision --autogenerate -m "$$msg"

# Run database seeder
seed:
	cd backend && python -m app.utils.seeder

# Run Pytest suite
test:
	cd backend && pytest -v app/tests

# Run code formatters and linters
lint:
	black backend/app
	isort backend/app
	flake8 backend/app --max-line-length=120 --exclude=migrations

# Build and start docker-compose
docker:
	docker-compose up --build

# Remove temporary files and cached structures
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf backend/dist backend/build backend/*.egg-info
