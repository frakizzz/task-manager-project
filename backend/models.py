from sqlalchemy import Column, Integer, String, ForeignKey, Text, Boolean, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    role = Column(String(50), default="Учасник команди") 
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="assignee")
    projects = relationship("Project", back_populates="owner")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), index=True, nullable=False)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="projects")
    tasks = relationship("Task", back_populates="project")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), index=True, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), default="New") 
    priority = Column(String(50), default="Medium")

    deadline = Column(DateTime, nullable=True) 

    project_id = Column(Integer, ForeignKey("projects.id")) 
    assignee_id = Column(Integer, ForeignKey("users.id")) 

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")