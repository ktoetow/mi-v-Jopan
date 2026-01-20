from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI(
    title="TutorBook",
    version="0.1.0"
)

app.mount('/static',StaticFiles(directory='static'), name='static')
templates=Jinja2Templates(directory='templates')

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Все работает"}

