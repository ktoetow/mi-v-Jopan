from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import asyncpg

app = FastAPI(
    title="TutorBook",
    version="0.1.0",
)

DB_URL = "postgresql://postgres:ktoeto1243@localhost:5432/tutorbook"
db_pool = None

async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)
    yield
    await db_pool.close()

app.mount('/static',StaticFiles(directory='static'), name='static')
templates=Jinja2Templates(directory='templates')

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/health")
async def health_check():
    try:
        async with db_pool.acquire() as conn:
            await conn.execute("SELECT 1")
        return {"status": "ok", "message": "Подключение к PostgreSQL работает"}
    except Exception as e:
        return {"status": "error", "message": f"Ошибка: {str(e)}"}