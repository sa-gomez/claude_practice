# Simple FastAPI Todo REST API

A REST API for managing todos using FastAPI with PostgreSQL database persistence.

## Setup

### 1. Start PostgreSQL Database

Using Docker Compose (recommended):
```bash
docker-compose up -d
```

Wait a few seconds for PostgreSQL to start and be ready.

### 2. Create and Activate Virtual Environment
```bash
python3 -m venv claude_practice_venv
source claude_practice_venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize Database

The database schema is created automatically on first server start, but you can also manually initialize it:
```bash
# Set database URL (optional, uses default if not set)
export DATABASE_URL="postgresql://todouser:todopass@localhost:5432/todos_db"

# Create tables
python init_db.py
```

### 5. Run the Server

**For Development** (with auto-reload):
```bash
# Database URL is set automatically if using default Docker Compose credentials
uvicorn main:app --reload
```

**For Production/Testing** (optimized performance):
```bash
# Use worker processes for multi-core utilization
# Optimized for 28-core CPU: 8 workers
uvicorn main:app --workers 8
```

The server will start at `http://localhost:8000`

### 6. Access API Documentation
Open your browser and navigate to `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### 7. Stop PostgreSQL (when done)
```bash
docker-compose down
```

To also remove the database volume:
```bash
docker-compose down -v
```

### Performance Notes

- **Development mode** (`--reload`): Single worker, auto-reloads on code changes
- **Production mode**: Use `--workers 8` for optimal performance
  - Single worker with database: ~400-700 req/s
  - 8 workers with database: ~2,400-3,800 req/s
  - Database adds latency compared to in-memory (~10-20% slower) but provides data persistence
  - See `test/results/` for detailed performance analysis and benchmarks

### Database

- **Database**: PostgreSQL 15 (Docker)
- **ORM**: SQLAlchemy 2.0
- **Connection Pooling**: Automatic (pool_size=10, max_overflow=20)
- **Data Persistence**: All todos persist across server restarts
- **Default Credentials**: User `todouser`, Password `todopass`, Database `todos_db`

## API Endpoints

### List All Todos
```
GET /todos
```
Returns a list of all todos.

### Get a Specific Todo
```
GET /todos/{todo_id}
```
Returns a specific todo by ID. Returns 404 if not found.

### Create a New Todo
```
POST /todos
```
Request body:
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread"
}
```
Returns the created todo with an auto-generated ID (status 201).

### Update a Todo
```
PUT /todos/{todo_id}
```
Request body (all fields optional):
```json
{
  "title": "Buy groceries",
  "description": "Milk, eggs, bread, butter",
  "completed": true
}
```
Returns the updated todo.

### Delete a Todo
```
DELETE /todos/{todo_id}
```
Deletes the todo. Returns 204 No Content on success, 404 if not found.

## Testing Examples

### Using curl
```bash
# Create a todo
curl -X POST "http://localhost:8000/todos" \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "description": "Build a REST API"}'

# Get all todos
curl "http://localhost:8000/todos"

# Get a specific todo
curl "http://localhost:8000/todos/1"

# Update a todo
curl -X PUT "http://localhost:8000/todos/1" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'

# Delete a todo
curl -X DELETE "http://localhost:8000/todos/1"
```

### Using Python requests
```python
import requests

BASE_URL = "http://localhost:8000"

# Create
response = requests.post(f"{BASE_URL}/todos", json={"title": "Learn FastAPI"})
todo = response.json()

# Get all
response = requests.get(f"{BASE_URL}/todos")
print(response.json())

# Update
response = requests.put(f"{BASE_URL}/todos/{todo['id']}", json={"completed": True})
print(response.json())

# Delete
requests.delete(f"{BASE_URL}/todos/{todo['id']}")
```

## Features

- ✅ Create, Read, Update, Delete (CRUD) operations
- ✅ PostgreSQL database for persistent data storage
- ✅ SQLAlchemy ORM for database operations
- ✅ Docker container setup for PostgreSQL
- ✅ Connection pooling for concurrent requests
- ✅ Automatic API documentation via FastAPI
- ✅ Proper error handling (404 for missing todos)
- ✅ Pydantic data validation
- ✅ Correct HTTP status codes (201 for create, 204 for delete)
- ✅ Data persists across server restarts

## Data Model

```json
{
  "id": 1,
  "title": "Learn FastAPI",
  "description": "Build a REST API",
  "completed": false
}
```

- `id`: Auto-generated integer
- `title`: Required string
- `description`: Optional string
- `completed`: Boolean (default: false)
