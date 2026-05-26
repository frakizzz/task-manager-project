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
    pass 

class Task(TaskBase):
    id: int
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None

    class Config:
        from_attributes = True

class TaskUpdateStatus(BaseModel):
    status: str

# ==========================================
# 2. СХЕМИ ПРОЄКТІВ (Projects)
# ==========================================
class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class Project(ProjectBase):
    id: int
    created_at: datetime
    owner_id: Optional[int] = None
    tasks: List[Task] = [] 

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

# НОВИЙ КЛАС ДЛЯ ЛОГІНУ (саме його не вистачало для main.py)
class UserLogin(BaseModel):
    username: str
    password: str

class User(UserBase):
    id: int
    is_active: bool

    class Config:
        from_attributes = True