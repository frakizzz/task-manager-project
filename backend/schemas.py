from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class AttachmentBase(BaseModel):
    filename: str
    file_path: str
    file_type: str

class AttachmentCreate(AttachmentBase):
    task_id: int

class Attachment(AttachmentBase):
    id: int
    uploaded_at: datetime
    task_id: int
    class Config:
        from_attributes = True

class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    pass

class CommentAuthor(BaseModel):
    username: str
    class Config:
        from_attributes = True

class Comment(CommentBase):
    id: int
    created_at: datetime
    task_id: int
    author_id: int
    author: Optional[CommentAuthor] = None 
    class Config:
        from_attributes = True

class LogBase(BaseModel):
    action: str
    details: str

class Log(LogBase):
    id: int
    timestamp: datetime
    project_id: int
    user_id: int
    user: Optional[CommentAuthor] = None
    class Config:
        from_attributes = True

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "New"
    priority: str = "Medium"
    tag: str = "Dev"
    deadline: Optional[datetime] = None

class TaskCreate(TaskBase):
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None  

class TaskUpdateStatus(BaseModel):
    status: str

class Task(TaskBase):
    id: int
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    attachments: List[Attachment] = []  
    comments: List[Comment] = []  
    class Config:
        from_attributes = True

class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    pass

class ProjectJoin(BaseModel):
    invite_code: str

class Project(ProjectBase):
    id: int
    invite_code: str
    created_at: datetime
    owner_id: int
    tasks: List["Task"] = []
    class Config:
        from_attributes = True

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