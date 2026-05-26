from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

# ==========================================
# 1. СХЕМИ ЗАДАЧ (Tasks)
# ==========================================
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "New"
    priority: str = "Medium"
    tag: str = "Розробка"
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    project_id: Optional[int] = None

class TaskUpdateStatus(BaseModel):
    status: str

class Task(TaskBase):
    id: int
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

    class Config:
        from_attributes = True

# ==========================================
# 2. СХЕМИ ПРОЄКТІВ (Projects)
# ==========================================
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

# Схема для приєднання до проєкту за кодом
class ProjectJoin(BaseModel):
    invite_code: str

class Project(ProjectBase):
    id: int
    invite_code: str
    created_at: datetime
    owner_id: int
    
    # Використовуємо string-формат для Tasks, щоб уникнути помилок циклічного імпорту, 
    # якщо Pydantic буде суворо перевіряти типи
    tasks: List["Task"] = []

    class Config:
        from_attributes = True

# ==========================================
# 3. СХЕМИ КОРИСТУВАЧІВ (Users)
# ==========================================
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "Учасник команди"

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True