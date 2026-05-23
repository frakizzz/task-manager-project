from fastapi import FastAPI
import models
from database import engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Task Manager API")

@app.get("/")
def read_root():
    return {"status": "success", "message": "Привіт! Сервер диплому та база даних зв'язані!"}