from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy import Float
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy import Date

from database import Base
from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    class Config:
        orm_mode = True

class UserCreate(BaseModel):
    username: str
    password: str

class TokenData(BaseModel):
    username: str

class UserOut(BaseModel):
    id: int
    username: str
    hashed_password: str

    class Config:
        orm_mode = True

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class ToDo(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    tasks = Column(String)
    subtasks = relationship("ToDo", backref=backref('parent', remote_side=[id]), cascade="all,delete")
    client = Column(String)
    client_id = Column(Integer)
    matter_id = Column(Integer)
    due_date = Column(Date)
    date_completed = Column(Date)
    time_spent = Column(Float)
    completed_bool = Column(Boolean, default=False)
    user_id = Column(Integer, ForeignKey('users.id'))
    parent_id = Column(Integer, ForeignKey('todos.id'))
    
def create_todo(db: Session, tasks: str, user_id: int, client: str, client_id: int, matter_id: int, due_date: Date, date_completed: Date, time_spent: Float, completed_bool: bool, parent_id: int = None):
    todo = ToDo(
        tasks=tasks, 
        user_id=user_id, 
        client=client, 
        client_id=client_id, 
        matter_id=matter_id, 
        due_date=due_date, 
        date_completed=date_completed,
        time_spent=time_spent, 
        completed_bool=completed_bool, 
        parent_id=parent_id
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo

def get_todo(db: Session, item_id: int):
    return db.query(ToDo).filter(ToDo.id == item_id).first()

def update_todo(db: Session, item_id: int, time_spent: float = 0.0, completed_bool: bool = False):
    todo = get_todo(db, item_id)
    todo.completed_bool = completed_bool
    todo.date_completed = datetime.today()
    todo.time_spent = time_spent
    db.commit()
    db.refresh(todo)
    return todo

def get_todos(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.user_id == user_id, ToDo.completed_bool == False).offset(skip).limit(limit).all()

def get_complete_todos(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.user_id == user_id, ToDo.completed_bool == True).offset(skip).limit(limit).all()

def delete_todo(db: Session, item_id: int):
    todo = get_todo(db, item_id)
    db.delete(todo)
    db.commit()

def search_todos(db: Session, user_id: int, query: str):
    return db.query(ToDo).filter(ToDo.user_id == user_id, ToDo.tasks.like(f"%{query}%")).all()
