
from fastapi import FastAPI, HTTPException, Request, Form
from pydantic import BaseModel
from typing import List, Optional
from uuid import uuid4, UUID
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pickle
import os
import openai

app = FastAPI()
templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    with open('static/index.html', 'r') as f:
        content = f.read()
    return HTMLResponse(content=content)

class ToDoItem(BaseModel):
    id: Optional[UUID] = None
    content: str
    completed: bool = False

class Subtask(BaseModel):
    description: str

class SubtasksResponse(BaseModel):
    subtasks: List[Subtask] = []

if os.path.exists('todo_items.pkl'):
    with open('todo_items.pkl', 'rb') as f:
        todo_items = pickle.load(f)
else:
    todo_items = []

if os.path.exists('completed_items.pkl'):
    with open('completed_items.pkl', 'rb') as f:
        completed_items = pickle.load(f)
else:
    completed_items = []

def save_lists():
    with open('todo_items.pkl', 'wb') as f:
        pickle.dump(todo_items, f)
    with open('completed_items.pkl', 'wb') as f:
        pickle.dump(completed_items, f)

@app.get("/todo/", response_class=HTMLResponse)
def read_todo_items(request: Request):
    return templates.TemplateResponse("todo.html", {"request": request, "items": todo_items})

@app.get("/todo/completed", response_class=HTMLResponse)
def read_completed_items(request: Request):
    return templates.TemplateResponse("completed.html", {"request": request, "items": completed_items})

@app.post("/todo/", response_model=ToDoItem)
def create_todo_item(content: str = Form(...)):
    item = ToDoItem(content=content, id=uuid4())
    todo_items.append(item)
    save_lists()
    return item

@app.put("/todo/{item_id}/complete", response_model=ToDoItem)
def complete_todo_item(item_id: UUID):
    for idx, item in enumerate(todo_items):
        if item.id == item_id:
            item.completed = True
            completed_item = todo_items.pop(idx)
            completed_items.append(completed_item)
            save_lists()
            return completed_item
    raise HTTPException(status_code=404, detail="Item not found")



@app.get("/todo/{item_id}", response_model=ToDoItem)
def read_todo_item(item_id: UUID):
    for item in todo_items:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/todo/{item_id}", response_model=ToDoItem)
def update_todo_item(item_id: UUID, item: ToDoItem):
    for idx, db_item in enumerate(todo_items):
        if db_item.id == item_id:
            todo_items[idx] = item
            item.id = item_id
            save_lists()
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/todo/{item_id}", response_model=ToDoItem)
def delete_todo_item(item_id: UUID):
    for idx, item in enumerate(todo_items):
        if item.id == item_id:
            todo_items.pop(idx)
            save_lists()
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/todo/completed/{item_id}", response_model=ToDoItem)
def delete_completed_item(item_id: UUID):
    for idx, item in enumerate(completed_items):
        if item.id == item_id:
            completed_items.pop(idx)
            save_lists()
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/autosubtask/", response_model=List[ToDoItem])
async def autosubtask(content: str = Form(...)):
    # You need to set your OpenAI API key here
    openai.api_key = ''

    # Send the task description to OpenAI's Chat completions endpoint
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": """ You are part of an ai assisted to-do app. You going to receive a 'to-do' task from a user, and then you are going to break this task down into subtasks. Return your response as json in the following format {
                    "subtasks": [
                        {
                            "description": "Subtask 1 description"
                        },
                        {
                            "description": "Subtask 2 description"
                        },
                        // More subtasks can be added here
                    ]
                }. Do not return anything other than json. Do not return an excessive amount of subtasks. This is for an attorney's timekeeping system, so use LEDES style entries."""},
            {"role": "user", "content": content}
        ]
    )

    # Parse the JSON response to get the subtasks
    subtasks_json = response.choices[0].message["content"]

    print(subtasks_json)
    # Here you need to parse the subtasks_json into your expected format
    subtasks_data = SubtasksResponse.parse_raw(subtasks_json)

    # Add the subtasks to your todo list
    new_subtasks = []
    for subtask in subtasks_data.subtasks:
        new_subtask = ToDoItem(content=subtask.description, id=uuid4())
        todo_items.append(new_subtask)
        new_subtasks.append(new_subtask)
    
    # Save the updated todo list
    save_lists()
    
    # Return the newly created subtasks
    return new_subtasks
