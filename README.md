# RBAC-RAG for ERP

This project is a secure and scalable ERP (Enterprise Resource Planning) system that uses a Retrieval Augmented Generation (RAG) model with Role-Based Access Control (RBAC).

## Documentation

All the documentation for this project is located in the `docs` directory.

## Development

To start the development environment, use the following command:

```bash
docker-compose up
```

## Database Migrations

This project uses Alembic for database migrations. Here's how to work with migrations:

### Prerequisites

Make sure you have the required dependencies installed:
```bash
cd backend
pip install -r requirements.txt
```

### Running Migrations

1. **Apply all migrations:**
   ```bash
   cd backend
   PYTHONPATH=/path/to/backend alembic upgrade head
   ```

2. **Create a new migration:**
   ```bash
   cd backend
   PYTHONPATH=/path/to/backend alembic revision --autogenerate -m "Description of changes"
   ```

3. **Check migration status:**
   ```bash
   cd backend
   PYTHONPATH=/path/to/backend alembic current
   ```

4. **Rollback to previous migration:**
   ```bash
   cd backend
   PYTHONPATH=/path/to/backend alembic downgrade -1
   ```

### Migration Files

- Migration files are located in `backend/alembic/versions/`
- Each migration has a unique revision ID and descriptive name
- The `alembic.ini` file contains database configuration
- The `alembic/env.py` file imports all models for autogeneration

### Troubleshooting

- **Database connection issues**: Check your `DATABASE_URL` environment variable
- **Import errors**: Ensure `PYTHONPATH` is set to the backend directory
- **SQLite limitations**: Some operations like `ALTER COLUMN` are not supported in SQLite

## Code Quality

### Backend (Python)

The backend uses Ruff for linting and Black for code formatting:

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Run linting
ruff check .

# Run formatting
black .

# Run both (using the provided script)
./scripts/lint.sh
```

### Frontend (React/TypeScript)

The frontend uses ESLint for linting and Prettier for code formatting:

```bash
cd frontend

# Install dependencies
npm install

# Run linting
npm run lint

# Fix linting issues
npm run lint:fix

# Run formatting
npm run format

# Check formatting
npm run format:check
```

## Testing

### Unit Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd frontend
npm test
```

### End-to-End Testing

Run the complete system test:

```bash
# From project root
./scripts/e2e-test.sh
```

This script will:
1. Start all services with docker-compose
2. Wait for services to be ready
3. Test backend health endpoints
4. Test frontend accessibility
5. Verify API endpoints are working
6. Provide a summary of the test results
