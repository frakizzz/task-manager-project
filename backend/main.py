import os
import shutil
import uuid
from fastapi import FastAPI, Request, Depends, HTTPException, status, Response, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import jwt
from typing import Optional
from datetime import datetime, timedelta

import models
import schemas
import crud
from database import engine, SessionLocal

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TeamTasker Pro API")

import sys

# Функція для визначення правильного шляху до файлів інтерфейсу
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        # Якщо запущено з exe, беремо файли з тимчасового простору компілятора
        return os.path.join(sys._MEIPASS, relative_path)
    # Якщо запускаємо локально, беремо з поточної папки
    return os.path.join(os.path.abspath("."), relative_path)

# База даних та завантаження файлів ПОВИННІ бути в реальній папці з exe, щоб дані не видалялися
BASE_DIR = os.path.dirname(sys.executable) if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Монтуємо папки інтерфейсу за допомогою нашого динамічного хелпера
app.mount("/static", StaticFiles(directory=get_resource_path("static")), name="static")
templates = Jinja2Templates(directory=get_resource_path("templates"))

SECRET_KEY = "teamtasker_super_secret_key_for_diploma"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[models.User]:
    token = request.cookies.get("access_token")
    if not token: return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None: return None
        return crud.get_user_by_username(db, username=username)
    except jwt.PyJWTError:
        return None

def log_action(db: Session, project_id: int, user_id: int, action: str, details: str):
    if project_id and user_id:
        new_log = models.Log(project_id=project_id, user_id=user_id, action=action, details=details)
        db.add(new_log)
        db.commit()

@app.get("/", response_class=HTMLResponse)
def read_landing(request: Request, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "current_user": current_user}
    )

@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if current_user:
        return RedirectResponse(url="/hub", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/logout")
def logout_user(response: Response):
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@app.get("/hub", response_class=HTMLResponse)
def read_hub(request: Request, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    owned_projects = current_user.owned_projects
    joined_projects = current_user.joined_projects

    return templates.TemplateResponse(
        request=request,
        name="hub.html", 
        context={
            "request": request, 
            "current_user": current_user.username,
            "owned_projects": owned_projects,
            "joined_projects": joined_projects
        }
    )

@app.get("/board", response_class=HTMLResponse)
def read_board(request: Request, project_id: int = None, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_projects = crud.get_user_projects(db, current_user.id)
    active_project = next((p for p in user_projects if p.id == project_id), None) if project_id else (user_projects[0] if user_projects else None)

    if active_project:
        all_tasks = active_project.tasks
        active_project_id = active_project.id
        active_project_name = active_project.title
        invite_code = active_project.invite_code
        team_members = [active_project.owner] + list(active_project.members)
    else:
        all_tasks = []
        active_project_id = None
        active_project_name = "NO_WORKSPACE_FOUND"
        invite_code = "N/A"
        team_members = []

    total = len(all_tasks)
    todo_count = sum(1 for t in all_tasks if t.status in ['New', 'To Do'])
    in_progress_count = sum(1 for t in all_tasks if t.status == 'In Progress')
    done_count = sum(1 for t in all_tasks if t.status == 'Done')
    progress = int((done_count / total) * 100) if total > 0 else 0
    
    return templates.TemplateResponse(
        request=request, name="board.html", context={
            "request": request, "tasks": all_tasks, "total": total, "todo": todo_count,
            "in_progress": in_progress_count, "done": done_count, "progress": progress,
            "current_user": current_user.username, "user_projects": user_projects, 
            "active_project_id": active_project_id, "active_project_name": active_project_name, 
            "invite_code": invite_code, "team_members": team_members
        }
    )

@app.get("/directory", response_class=HTMLResponse)
def read_directory(request: Request, project_id: int = None, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_projects = crud.get_user_projects(db, current_user.id)
    active_project = next((p for p in user_projects if p.id == project_id), None) if project_id else (user_projects[0] if user_projects else None)

    if not active_project:
        return RedirectResponse(url="/hub", status_code=status.HTTP_302_FOUND)

    team = []
    
    owner_tasks = db.query(models.Task).filter(models.Task.project_id == active_project.id, models.Task.assignee_id == active_project.owner_id).count()
    team.append({
        "id": active_project.owner.id,
        "username": active_project.owner.username,
        "role": "OWNER",
        "task_count": owner_tasks
    })

    for member in active_project.members:
        member_tasks = db.query(models.Task).filter(models.Task.project_id == active_project.id, models.Task.assignee_id == member.id).count()
        team.append({
            "id": member.id,
            "username": member.username,
            "role": "MEMBER",
            "task_count": member_tasks
        })

    return templates.TemplateResponse(
        request=request, name="directory.html", context={
            "request": request, "current_user": current_user.username,
            "user_projects": user_projects, "active_project_id": active_project.id, 
            "active_project_name": active_project.title, "invite_code": active_project.invite_code, 
            "team": team, "is_owner": current_user.id == active_project.owner_id
        }
    )

@app.get("/logs", response_class=HTMLResponse)
def read_logs(request: Request, project_id: int = None, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    user_projects = crud.get_user_projects(db, current_user.id)
    active_project = next((p for p in user_projects if p.id == project_id), None) if project_id else (user_projects[0] if user_projects else None)
    
    if not active_project:
        return RedirectResponse(url="/hub", status_code=status.HTTP_302_FOUND)

    sys_logs = db.query(models.Log).filter(models.Log.project_id == active_project.id).order_by(models.Log.timestamp.desc()).limit(100).all()

    return templates.TemplateResponse(
        request=request, name="logs.html", context={
            "request": request, "current_user": current_user.username, "user_projects": user_projects, 
            "active_project_id": active_project.id, "active_project_name": active_project.title, 
            "sys_logs": sys_logs
        }
    )

@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if crud.get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Користувач з таким іменем вже існує")
    crud.create_user(db=db, user=user)
    return {"message": "Реєстрація успішна!"}

@app.post("/login")
def login_user(response: Response, user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    if not db_user or not crud.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")
    
    access_token = create_access_token(data={"sub": db_user.username})
    response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=3600, samesite="lax")
    return {"message": "Успішний вхід!"}

@app.post("/projects/", response_model=schemas.Project)
def create_new_project(project: schemas.ProjectCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user: 
        raise HTTPException(status_code=401)
        
    new_proj = crud.create_project(db=db, project=project, owner_id=current_user.id)
    log_action(db, new_proj.id, current_user.id, "INIT", "Створено новий робочий простір")
    
    return new_proj

@app.post("/projects/join")
def join_project(data: schemas.ProjectJoin, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user: 
        raise HTTPException(status_code=401)
        
    project = crud.join_project_by_code(db=db, invite_code=data.invite_code, user_id=current_user.id)
    if not project: 
        raise HTTPException(status_code=404)
        
    log_action(db, project.id, current_user.id, "JOIN", "Користувач приєднався за інвайт-кодом")
    return {"message": f"Успішно приєднано"}

@app.delete("/projects/{project_id}")
def delete_project_endpoint(project_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user: 
        raise HTTPException(status_code=401)
        
    success = crud.delete_project(db, project_id, current_user.id)
    if not success: 
        raise HTTPException(status_code=403, detail="Not authorized or not found")
        
    return {"message": "Deleted"}

@app.post("/projects/{project_id}/leave")
def leave_project_endpoint(project_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user: 
        raise HTTPException(status_code=401)
        
    success = crud.leave_project(db, project_id, current_user.id)
    if not success: 
        raise HTTPException(status_code=400, detail="Cannot leave")
        
    return {"message": "Left"}

@app.delete("/projects/{project_id}/kick/{user_id}")
def kick_user(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user: 
        raise HTTPException(status_code=401)
    
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project: 
        raise HTTPException(status_code=404)
        
    if project.owner_id != current_user.id: 
        raise HTTPException(status_code=403, detail="SYS_ERR: OWNER_PRIVILEGE_REQUIRED")
    
    user_to_kick = db.query(models.User).filter(models.User.id == user_id).first()
    if not user_to_kick or user_to_kick not in project.members:
        raise HTTPException(status_code=404, detail="SYS_ERR: USER_NOT_FOUND")

    project.members.remove(user_to_kick)
 
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id, models.Task.assignee_id == user_id).all()
    for t in tasks:
        t.assignee_id = None
        
    log_action(db, project_id, current_user.id, "KICK", f"Користувача {user_to_kick.username} видалено з проєкту")
    db.commit()
    return {"message": "SYS_SUCCESS: USER_TERMINATED"}

@app.post("/tasks/", response_model=schemas.Task)
def create_new_task(task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    new_task = crud.create_task(db=db, task=task)
    
    if current_user and task.project_id:
        log_action(db, task.project_id, current_user.id, "CREATE_TASK", f"Створено задачу: {task.title}")
        
    return new_task

@app.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tasks(db, skip=skip, limit=limit)

@app.patch("/tasks/{task_id}/status")
def update_status(task_id: int, status_data: schemas.TaskUpdateStatus, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if task and current_user:
        log_action(db, task.project_id, current_user.id, "MOVE_TASK", f"Задача #{task.id} переміщена в {status_data.status.upper()}")
        
    return crud.update_task_status(db=db, task_id=task_id, new_status=status_data.status)

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task_full(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    updated_task = crud.update_task_details(db=db, task_id=task_id, task_data=task)
    if not updated_task: 
        raise HTTPException(status_code=404)
        
    if current_user:
        log_action(db, updated_task.project_id, current_user.id, "EDIT_TASK", f"Оновлено дані задачі #{task_id}")
        
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    
    if task and current_user:
        log_action(db, task.project_id, current_user.id, "DELETE_TASK", f"Задачу #{task.id} видалено (WARNING)")
        
    deleted = crud.delete_task(db=db, task_id=task_id)
    if not deleted: 
        raise HTTPException(status_code=404)
        
    return {"message": "Успішно видалено"}

@app.post("/tasks/{task_id}/attachments", response_model=schemas.Attachment)
def upload_attachment(task_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не знайдена")

    file_extension = file.filename.split(".")[-1].lower() if "." in file.filename else ""
    unique_filename = f"{uuid.uuid4().hex}.{file_extension}" if file_extension else uuid.uuid4().hex
    file_path = os.path.join(UPLOAD_DIR, unique_filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    if file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
        file_type = "image"
    elif file_extension in ['mp4', 'webm', 'mov']:
        file_type = "video"
    else:
        file_type = "document"

    attachment = models.Attachment(
        filename=file.filename,
        file_path=f"/static/uploads/{unique_filename}",
        file_type=file_type,
        task_id=task_id
    )
    db.add(attachment)
    db.commit()
    db.refresh(attachment)
    return attachment

@app.post("/tasks/{task_id}/comments", response_model=schemas.Comment)
def add_comment(task_id: int, comment: schemas.CommentCreate, db: Session = Depends(get_db), current_user: Optional[models.User] = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Unauthorized")
        
    task = db.query(models.Task).filter(models.Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Задача не знайдена")

    new_comment = models.Comment(
        text=comment.text,
        task_id=task_id,
        author_id=current_user.id
    )
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    return new_comment