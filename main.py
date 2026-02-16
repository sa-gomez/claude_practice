from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="Todo API", description="A simple REST API for managing todos")

# Data model
class Todo(BaseModel):
    id: Optional[int] = None
    title: str
    description: Optional[str] = None
    completed: bool = False

class TodoCreate(BaseModel):
    title: str
    description: Optional[str] = None

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

# In-memory storage
todos: List[dict] = []
next_id = 1

# Helper function to find todo by ID
def get_todo_by_id(todo_id: int):
    for todo in todos:
        if todo["id"] == todo_id:
            return todo
    return None

# Endpoints
@app.get("/todos", response_model=List[Todo])
def list_todos():
    """Get all todos"""
    return todos

@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int):
    """Get a specific todo by ID"""
    todo = get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo

@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(todo_create: TodoCreate):
    """Create a new todo"""
    global next_id
    new_todo = {
        "id": next_id,
        "title": todo_create.title,
        "description": todo_create.description,
        "completed": False
    }
    todos.append(new_todo)
    next_id += 1
    return new_todo

@app.put("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, todo_update: TodoUpdate):
    """Update a todo"""
    todo = get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    if todo_update.title is not None:
        todo["title"] = todo_update.title
    if todo_update.description is not None:
        todo["description"] = todo_update.description
    if todo_update.completed is not None:
        todo["completed"] = todo_update.completed

    return todo

@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int):
    """Delete a todo"""
    todo = get_todo_by_id(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    todos.remove(todo)
    return None

@app.get("/", tags=["Root"])
def root():
    """Welcome message"""
    return {"message": "Welcome to the Todo API! Visit /docs for interactive API documentation"}
