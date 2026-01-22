from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from contextlib import asynccontextmanager
from database import engine, get_db  

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@asynccontextmanager
async def lifespan(app: FastAPI):
    
    from models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
   
    await engine.dispose()

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
        async with get_db() as session:  
            await session.execute("SELECT 1")
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
        async with get_db() as session:  
            await session.execute(
                """
                INSERT INTO users (full_name, email, password_hash)
                VALUES (:full_name, :email, :password_hash)
                """,
                {
                    "full_name": full_name,
                    "email": email,
                    "password_hash": hashed_pw
                }
            )
            await session.commit()  
        return JSONResponse(
            content={"status": "success", "message": "Пользователь успешно зарегистрирован"},
            status_code=201
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)