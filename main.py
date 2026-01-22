from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
import asyncpg

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DB_URL = "postgresql://postgres:ktoeto1243@localhost:5432/tutorbook"
db_pool = None

async def lifespan(app: FastAPI):
    global db_pool
    db_pool = await asyncpg.create_pool(DB_URL)
    yield
    await db_pool.close()

app = FastAPI(
    title="TutorBook",
    version="0.1.0",
    lifespan=lifespan
)

app.mount('/static', StaticFiles(directory='static'), name='static')
templates = Jinja2Templates(directory='templates')

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

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

@app.post("/api/register")
async def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...)
):
    hashed_pw = hash_password(password)

    try:
        async with db_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO users (full_name, email, password_hash)
                VALUES ($1, $2, $3)
                """,
                full_name, email, hashed_pw
            )
        return JSONResponse(
            content={"status": "success", "message": "Пользователь успешно зарегистрирован"},
            status_code=201
        )
    except asyncpg.exceptions.UniqueViolationError:
        raise HTTPException(status_code=400, detail="Пользователь с таким email уже существует")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")