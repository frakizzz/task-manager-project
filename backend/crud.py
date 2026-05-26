from sqlalchemy.orm import Session
import bcrypt
import models
import schemas

def get_tasks(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Task).offset(skip).limit(limit).all()

def create_task(db: Session, task: schemas.TaskCreate, project_id: int = None):
    db_task = models.Task(**task.model_dump(), project_id=project_id)
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
        db.commit()
        db.refresh(db_task)
    return db_task

def delete_task(db: Session, task_id: int):
    db_task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if db_task:
        db.delete(db_task)
        db.commit()
    return db_task

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    # Шифруємо пароль через чистий bcrypt
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