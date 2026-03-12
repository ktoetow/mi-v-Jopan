from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse 
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

from database import engine, SessionLocal, Base
from models import User
from schemas import UserCreate

Base.metadata.create_all(bind=engine)

app = FastAPI(title="TutorBook")
# Исправляем путь к шаблонам
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")
)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    user = db.query(User).filter(User.id == user_id).first()
    return user

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@app.get("/api/health")
async def health_check():
    return {
        "status": "ok",
        "database": "connected",
        "message": "TutorBook backend is running!"
    }

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.post("/api/register")
async def register_user(
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    # Лёгкая серверная валидация, чтобы HTML-форма не создавала мусор
    user = UserCreate(full_name=full_name, email=email, password=password)

    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        # Возвращаем на страницу регистрации с сообщением
        return RedirectResponse(
            url="/register?error=Email%20already%20registered",
            status_code=303,
        )

    hashed_password = pwd_context.hash(user.password)

    db_user = User(
        full_name=user.full_name,
        email=user.email,
        password_hash=hashed_password,
        role="student"  # Добавляем роль по умолчанию
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return RedirectResponse(url="/login?success=registered", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)
    return templates.TemplateResponse("auth/login.html", {"request": request})

@app.post("/api/login")
async def login_user(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    request.session["user_id"] = user.id
    # Добавляем роль в сессию
    request.session["user_role"] = user.role
    request.session["user_name"] = user.full_name
    
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Проверяем роль
    if user.role == "admin":
        template = "dashboard/admin.html"
    elif user.role == "tutor":
        template = "dashboard/tutor.html"
    else:
        template = "dashboard/student.html"
    
    return templates.TemplateResponse(template, {"request": request, "user": user})

@app.get("/about", response_class=HTMLResponse)
async def about_page(request: Request):
    return templates.TemplateResponse("about.html", {"request": request})

@app.get("/blog", response_class=HTMLResponse)
async def blog_page(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request})

@app.get("/contact", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse("contact.html", {"request": request})

@app.get("/for-tutors", response_class=HTMLResponse)
async def for_tutors_page(request: Request):
    return templates.TemplateResponse("for-tutors.html", {"request": request})

@app.get("/how-it-works", response_class=HTMLResponse)
async def how_it_works_page(request: Request):
    return templates.TemplateResponse("how-it-works.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)
    
    user = db.query(User).filter(User.id == user_id).first()
   
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user
    })

@app.get("/reviews", response_class=HTMLResponse)
async def reviews_page(request: Request):
    return templates.TemplateResponse("reviews.html", {"request": request})

@app.get("/subjects", response_class=HTMLResponse)
async def subjects_page(request: Request):
    return templates.TemplateResponse("subjects.html", {"request": request})

@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    return templates.TemplateResponse("support.html", {"request": request})

@app.get("/tutor-detail/{tutor_id}", response_class=HTMLResponse)
async def tutor_detail_page(request: Request, tutor_id: int):
    return templates.TemplateResponse("tutor_detail.html", {"request": request, "tutor_id": tutor_id})

@app.get("/tutors", response_class=HTMLResponse)
async def tutors_page(request: Request):
    return templates.TemplateResponse("tutors.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)