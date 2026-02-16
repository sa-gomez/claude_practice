# Simple FastAPI Todo REST API

A simple REST API for managing todos using FastAPI.

## Setup

### 1. Create and Activate Virtual Environment
```bash
python3 -m venv claude_practice_venv
source claude_practice_venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Server

**For Development** (with auto-reload):
```bash
uvicorn main:app --reload
```

**For Production/Testing** (optimized performance):
```bash
# Use worker processes for multi-core utilization
# Recommended: (2 × CPU_cores) + 1
# Example for 28-core CPU:
uvicorn main:app --workers 16
```

The server will start at `http://localhost:8000`

### 4. Access API Documentation
Open your browser and navigate to `http://localhost:8000/docs` for interactive API documentation (Swagger UI).

### Performance Notes

- **Development mode** (`--reload`): Single worker, auto-reloads on code changes
- **Production mode**: Use `--workers N` to utilize multiple CPU cores
  - Single worker: ~70 req/s
  - 16 workers: ~10,750 req/s (160x improvement!)
  - See `test/results/` for detailed performance analysis

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
- ✅ In-memory storage (data resets on server restart)
- ✅ Automatic API documentation via FastAPI
- ✅ Proper error handling (404 for missing todos)
- ✅ Pydantic data validation
- ✅ Correct HTTP status codes (201 for create, 204 for delete)

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
