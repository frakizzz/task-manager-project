from sqlalchemy.orm import Session
import bcrypt
import uuid
import models
import schemas

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    pwd_bytes = user.password.encode('utf-8')[:72]
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    
    db_user = models.User(
        username=user.username, 
        email=user.email, 
        hashed_password=hashed.decode('utf-8'),
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str):
    pwd_bytes = plain_password.encode('utf-8')[:72]
    return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))

def create_project(db: Session, project: schemas.ProjectCreate, owner_id: int):
    unique_code = str(uuid.uuid4()).split('-')[0].upper()
    while db.query(models.Project).filter(models.Project.invite_code == unique_code).first():
        unique_code = str(uuid.uuid4()).split('-')[0].upper()

    db_project = models.Project(
        title=project.title,
        description=project.description,
        invite_code=unique_code,
        owner_id=owner_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project

def join_project_by_code(db: Session, invite_code: str, user_id: int):
    project = db.query(models.Project).filter(models.Project.invite_code == invite_code.upper()).first()
    if not project:
        return None
    if project.owner_id == user_id or any(member.id == user_id for member in project.members):
        return project
        
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user:
        project.members.append(user)
        db.commit()
        db.refresh(project)
    return project

def get_user_projects(db: Session, user_id: int):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        return []
    return list(user.owned_projects) + list(user.joined_projects)

def delete_project(db: Session, project_id: int, user_id: int):
    project = db.query(models.Project).filter(models.Project.id == project_id, models.Project.owner_id == user_id).first()
    if project:
        db.delete(project)
        db.commit()
        return True
    return False

def leave_project(db: Session, project_id: int, user_id: int):
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if project and user in project.members:
        project.members.remove(user)
        db.commit()
        return True
    return False

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate):
    db_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        priority=task.priority,
        tag=task.tag,
        deadline=task.deadline,
        project_id=task.project_id,
        assignee_id=task.assignee_id
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task_status(db: Session, task_id: int, new_status: str):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db_task.status = new_status
        db.commit()
        db.refresh(db_task)
    return db_task

def update_task_details(db: Session, task_id: int, task_data: schemas.TaskCreate):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db_task.title = task_data.title
        db_task.description = task_data.description
        db_task.priority = task_data.priority
        db_task.tag = task_data.tag
        db_task.project_id = task_data.project_id
        db_task.assignee_id = task_data.assignee_id
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task