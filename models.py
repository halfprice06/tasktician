from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Session
from sqlalchemy.orm import relationship
from sqlalchemy.orm import backref
from sqlalchemy import Date

from database import Base
from pydantic import BaseModel

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
    content = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'))
    completed = Column(Boolean, default=False)
    parent_id = Column(Integer, ForeignKey('todos.id'))
    subtasks = relationship("ToDo", backref=backref('parent', remote_side=[id]))
    client = Column(String)
    date = Column(Date)


def create_todo(db: Session, content: str, user_id: int, client: str, date: Date, parent_id: int = None):
    todo = ToDo(content=content, user_id=user_id, client=client, date=date, parent_id=parent_id)
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


def get_todo(db: Session, item_id: int):
    return db.query(ToDo).filter(ToDo.id == item_id).first()


def update_todo(db: Session, item_id: int, completed: bool = False):
    todo = get_todo(db, item_id)
    todo.completed = completed
    db.commit()
    db.refresh(todo)
    return todo


def get_todos(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.user_id == user_id, ToDo.completed == False).offset(skip).limit(limit).all()

def get_complete_todos(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(ToDo).filter(ToDo.user_id == user_id, ToDo.completed == True).offset(skip).limit(limit).all()

def delete_todo(db: Session, item_id: int):
    todo = get_todo(db, item_id)
    db.delete(todo)
    db.commit()

