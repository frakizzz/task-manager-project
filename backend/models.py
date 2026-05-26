from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, DateTime, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

# Проміжна таблиця для зв'язку багатьох до багатьох (Користувачі <-> Проєкти)
project_members = Table(
    "project_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="User")
    is_active = Column(Boolean, default=True)

    # Проєкти, якими володіє цей користувач (створив сам)
    owned_projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")
    
    # Проєкти, до яких користувач приєднався як учасник за кодом запрошення
    joined_projects = relationship("Project", secondary=project_members, back_populates="members")

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Код запрошення, як у Google Classroom (унікальний для кожного проєкту)
    invite_code = Column(String, unique=True, index=True, nullable=False)
    
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    
    # Зв'язки
    owner = relationship("User", back_populates="owned_projects")
    members = relationship("User", secondary=project_members, back_populates="joined_projects")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String, nullable=True)
    status = Column(String, default="New")
    priority = Column(String, default="Medium")
    tag = Column(String, default="Розробка")
    deadline = Column(DateTime, nullable=True)
    
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Зв'язки
    project = relationship("Project", back_populates="tasks")