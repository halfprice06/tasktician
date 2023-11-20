from datetime import datetime, timedelta
from fastapi import Depends, FastAPI, Form, HTTPException, Request, Response, status, Cookie, Body
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.security import OAuth2PasswordBearer
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
import logging  # Add this line for logging
import os

import models  # Add this line

from database import Base, SessionLocal, engine
from models import create_todo, delete_todo, get_todo, update_todo, User, UserCreate, UserOut

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

Base.metadata.create_all(bind=engine)

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.info('This will get logged to a file')


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def verify_password(password: str, hashed_password: str):
    return CryptContext().verify(password, hashed_password)

def get_token_from_cookie(access_token: Optional[str] = Cookie(None)):
    print(f"Cookie: {access_token}")  # Print the entire cookie
    return access_token

def get_current_user(token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)):
    print(f"Token: {token}")  # Print the token   
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = models.TokenData(username=username)
    except JWTError as e:
        print(f"JWTError: {e}")  # Log the error message
        raise credentials_exception
    user = get_user(db, username=token_data.username)  # Corrected line
    print(f"User from database: {user}")  # Print the user from database
    if user is None:
        raise credentials_exception
    return user

def get_current_user_or_none(token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)):
    try:
        return get_current_user(token, db)
    except HTTPException:
        return None

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(password: str, hashed_password: str):
    return pwd_context.verify(password, hashed_password)

def validate_email(username):
    if '@' not in username:
        return True


@app.get("/", response_class=HTMLResponse)
def login(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})


@app.get("/home", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user_or_none)):
    if current_user is None:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    todos = models.get_todos(db, current_user.id)
    context = {
        "request": request,
        "todos": todos,
        "title": "Home",
        "username": current_user.username
    }
    return templates.TemplateResponse("home.html", context)

@app.post("/add", response_class=HTMLResponse)
def add_todo(request: Request, 
             tasks: str = Form(...), 
             client: str = Form(None), 
             client_id: int = Form(None),
             matter_id: int = Form(None),
             due_date: date = Form(None),
             date_completed: date = Form(None),
             time_spent: float = Form(None),
             completed_bool: bool = Form(None),
             parent_id: int = Form(None),
             db: Session = Depends(get_db), 
             current_user: User = Depends(get_current_user)):
    client = client if client != "" else None  # If client is an empty string, put null into db
    print("test" + tasks, client, client_id, matter_id, due_date, date_completed, time_spent, completed_bool, parent_id)
    create_todo(db, tasks=tasks, user_id=current_user.id, client=client, client_id=client_id, matter_id=matter_id, due_date=due_date, date_completed=date_completed, time_spent=time_spent, completed_bool=completed_bool, parent_id=parent_id)
    todos = models.get_todos(db, current_user.id)  # Get all todos
    context = {"request": request, "items": todos}  # Change "item" to "items"
    return templates.TemplateResponse("in_progress.html", context)

@app.post("/add_new_completed", response_class=HTMLResponse)
def add_new_completed(request: Request, 
                      tasks: str = Form(...), 
                      client: str = Form(None), 
                      client_id: int = Form(None),
                      matter_id: int = Form(None),
                      due_date: date = Form(None),
                      date_completed: date = Form(None),
                      time_spent: float = Form(None),
                      parent_id: int = Form(None),
                      db: Session = Depends(get_db), 
                      current_user: User = Depends(get_current_user)):
    client = client if client != "" else None  # If client is an empty string, put null into db
    print("test" + tasks, client, client_id, matter_id, due_date, date_completed, time_spent, True, parent_id)
    create_todo(db, tasks=tasks, user_id=current_user.id, client=client, client_id=client_id, matter_id=matter_id, due_date=due_date, date_completed=date_completed, time_spent=time_spent, completed_bool=True, parent_id=parent_id)
    todos = models.get_todos(db, current_user.id)  # Get all todos
    context = {"request": request, "items": todos}  # Change "item" to "items"
    return templates.TemplateResponse("completed.html", context)

@app.get("/get_all_todos", response_class=HTMLResponse)
def get_all_todos(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = models.get_todos(db, current_user.id)
    context = {"request": request, "items": todos, "username": current_user.username}
    return templates.TemplateResponse("in_progress.html", context)

@app.get("/get_all_complete_todos", response_class=HTMLResponse)
def get_all_complete_todos(request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = models.get_complete_todos(db, current_user.id)
    context = {"request": request, "items": todos, "username": current_user.username}
    return templates.TemplateResponse("completed.html", context)

@app.post("/search", response_class=HTMLResponse)
def search(request: Request, query: str = Form(None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    todos = models.search_todos(db, current_user.id, query)
    context = {"request": request, "items": todos, "username": current_user.username}
    print(f"Search results: {todos}")  # Print the search results
    return templates.TemplateResponse("search_results.html", context)


@app.get("/edit/{item_id}", response_class=HTMLResponse)
def get_edit(request: Request, item_id: int, db: Session = Depends(get_db)):
    todo = get_todo(db, item_id)
    context = {"request": request, "todo": todo}
    return templates.TemplateResponse("todo.html", context)

@app.delete("/delete", response_class=HTMLResponse)
def delete(request: Request, item_ids: List[int] = Body(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for item_id in item_ids:
        delete_todo(db, item_id)
    todos = models.get_todos(db, current_user.id)  # Get all todos after deletion
    context = {"request": request, "items": todos}  # Change "item" to "items"
    return templates.TemplateResponse("in_progress.html", context)

@app.post("/mark_complete", response_class=HTMLResponse)
def mark_complete(request: Request, item_ids: List[int] = Body(...), time_spent: List[Optional[float]] = Body(default=None), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    print(f"Item IDs: {item_ids}")  # Print the item IDs
    print(f"Time spent: {time_spent}")  # Print the time spent
    
    for item_id, time in zip(item_ids, time_spent):
        todo = update_todo(db, item_id, time_spent=time, completed_bool=True)
    context = {"request": request, "item": todo}
    return templates.TemplateResponse("completed.html", context)

@app.post("/register", response_class=HTMLResponse)
def create_user(request: Request, username: str = Form(...), password: str = Form(...), confirm_password: str = Form(...), registration_code: str = Form(...), db: Session = Depends(get_db)):
    # # Check if username is a valid email address
    # if validate_email(username) == False:
    #     pass
    # else:
    #     # email is not valid, return error message
    #     return templates.TemplateResponse("registration_failure_invalid_email.html", {"request": request})
    # Check if username already exists in the database
    existing_user = get_user(db, username)
    if existing_user:
        return templates.TemplateResponse("registration_failure_username_exists.html", {"request": request})
    if registration_code != "getinwearegoingforaride":  # replace with your actual registration code
        return templates.TemplateResponse("registration_failure_wrong_code.html", {"request": request})
    if password != confirm_password:
        return templates.TemplateResponse("registration_failure_passwords_no_match.html", {"request": request})
    hashed_password = get_password_hash(password)
    db_user = models.User(username=username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return templates.TemplateResponse("registration_successful.html", {"request": request})

@app.get("/login", response_class=HTMLResponse)
def load_login_page(request: Request, response: Response):
    if "access_token" in request.cookies:
        access_token = request.cookies.get("access_token")
        try:
            payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username is not None:
                return RedirectResponse(url="/home", status_code=status.HTTP_302_FOUND)
        except JWTError:
            pass
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/get_register_box", response_class=HTMLResponse)
def get_register_box(request: Request, response: Response):
    return templates.TemplateResponse("register_container.html", {"request": request})

@app.post("/login", response_class=HTMLResponse)
def submit_login_form(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = get_user(db, username)
    if db_user is None or not verify_password(password, db_user.hashed_password):
        return templates.TemplateResponse("incorrect_password.html", {"request": request})

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    print(f"Access Token: {access_token}")  # Print the access token

    response = Response(status_code=status.HTTP_200_OK)
    response.headers["HX-Redirect"] = "/home"
    response.set_cookie("access_token", access_token, httponly=True)
    
    return response

@app.get("/logout")
def logout(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

@app.get("/test-token")
def test_token():
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": "testuser"}, expires_delta=access_token_expires
    )
    return {"access_token": access_token}

@app.get("/test-decode")
def test_decode(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        return {"error": str(e)}