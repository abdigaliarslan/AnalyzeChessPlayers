from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from backend.db import engine
from backend.models import Base
from backend.routes import router
from backend import models

models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")

app = FastAPI()

app.include_router(router)


@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register")
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/services")
async def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})