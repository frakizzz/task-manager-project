from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import engine, SessionLocal

# Створюємо таблиці в базі даних
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="TeamTasker Pro API")

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ==========================================
# МАРШРУТИ ДЛЯ СТОРІНОК (HTML)
# ==========================================

@app.get("/", response_class=HTMLResponse)
def read_landing(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/login", response_class=HTMLResponse)
def read_login(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@app.get("/board", response_class=HTMLResponse)
def read_board(request: Request, db: Session = Depends(get_db)):
    all_tasks = crud.get_tasks(db)
    total = len(all_tasks)
    todo_count = sum(1 for t in all_tasks if t.status in ['New', 'To Do'])
    in_progress_count = sum(1 for t in all_tasks if t.status == 'In Progress')
    done_count = sum(1 for t in all_tasks if t.status == 'Done')
    progress = int((done_count / total) * 100) if total > 0 else 0
    
    return templates.TemplateResponse(
        request=request, 
        name="board.html", 
        context={
            "request": request, 
            "tasks": all_tasks,
            "total": total,
            "todo": todo_count,
            "in_progress": in_progress_count,
            "done": done_count,
            "progress": progress
        }
    )

# ==========================================
# API: РЕЄСТРАЦІЯ ТА АВТОРИЗАЦІЯ
# ==========================================

@app.post("/register")
def register_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Перевіряємо, чи не зайнятий логін
    db_user = crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Користувач з таким іменем вже існує")
    
    crud.create_user(db=db, user=user)
    return {"message": "Реєстрація успішна!"}

@app.post("/login")
def login_user(user: schemas.UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_username(db, username=user.username)
    # Перевірка пароля через нову функцію verify_password (bcrypt)
    if not db_user or not crud.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Невірний логін або пароль")
    
    return {"message": "Успішний вхід!"}

# ==========================================
# API: ЗАДАЧІ
# ==========================================

@app.post("/tasks/", response_model=schemas.Task)
def create_new_task(task: schemas.TaskCreate, db: Session = Depends(get_db)):
    return crud.create_task(db=db, task=task)

@app.get("/tasks/", response_model=list[schemas.Task])
def read_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_tasks(db, skip=skip, limit=limit)

@app.patch("/tasks/{task_id}/status")
def update_status(task_id: int, status_data: schemas.TaskUpdateStatus, db: Session = Depends(get_db)):
    return crud.update_task_status(db=db, task_id=task_id, new_status=status_data.status)

@app.put("/tasks/{task_id}", response_model=schemas.Task)
def update_task_full(task_id: int, task: schemas.TaskCreate, db: Session = Depends(get_db)):
    updated_task = crud.update_task_details(db=db, task_id=task_id, task_data=task)
    if not updated_task:
        raise HTTPException(status_code=404, detail="Задачу не знайдено")
    return updated_task

@app.delete("/tasks/{task_id}")
def delete_task_endpoint(task_id: int, db: Session = Depends(get_db)):
    deleted = crud.delete_task(db=db, task_id=task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Задачу не знайдено")
    return {"message": "Успішно видалено"}