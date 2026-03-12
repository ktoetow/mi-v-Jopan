from fastapi import FastAPI, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse 
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import inspect, text
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

from database import engine, SessionLocal, Base
from models import User
Base.metadata.create_all(bind=engine)

app = FastAPI(title="TutorBook")

templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("SECRET_KEY", "your-secret-key-here")
)

app.mount("/static", StaticFiles(directory="static"), name="static")

TUTORS = {
    1: {
        "id": 1,
        "full_name": "Анна Петрова",
        "subjects": ["Математика"],
        "grades": ["5–7", "8–9"],
        "exams": ["ОГЭ"],
        "experience": 8,
        "price": 800,
        "bio": "Стаж 8 лет, подготовка к ОГЭ и повышение успеваемости. Объясняю спокойно и структурно, даю понятные алгоритмы и много практики.",
        "slots": [
            {"label": "26 янв, 15:00", "status": "available"},
            {"label": "26 янв, 17:00", "status": "available"},
            {"label": "27 янв, 14:00", "status": "booked"},
        ],
    },
    2: {
        "id": 2,
        "full_name": "Иван Сидоров",
        "subjects": ["Физика"],
        "grades": ["8–9", "10–11"],
        "exams": ["ЕГЭ"],
        "experience": 10,
        "price": 1000,
        "bio": "Кандидат наук, опыт 10 лет. Подготовка к ЕГЭ и олимпиадам. Работаю на понимание: теория + задачи с разбором типичных ошибок.",
        "slots": [
            {"label": "26 янв, 16:00", "status": "available"},
            {"label": "28 янв, 18:00", "status": "available"},
            {"label": "29 янв, 12:00", "status": "booked"},
        ],
    },
}

def ensure_user_role_column():
    inspector = inspect(engine)
    try:
        cols = inspector.get_columns("users")
    except Exception:
        return

    if any(c.get("name") == "role" for c in cols):
        return

    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'student'"))
        conn.execute(text("UPDATE users SET role = 'student' WHERE role IS NULL OR role = ''"))

ensure_user_role_column()

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

@app.get("/favicon.ico")
async def favicon():
    return RedirectResponse(url="/static/favicon.svg", status_code=307)

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

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/tutors", status_code=303)
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
        return templates.TemplateResponse(
            "auth/login.html",
            {"request": request, "error": "Неверный email или пароль", "email": email},
            status_code=400,
        )
    
    request.session["user_id"] = user.id
    request.session["user_role"] = user.role
    request.session["user_name"] = user.full_name
    
    return RedirectResponse(url="/tutors", status_code=303)

@app.get("/api/login")
async def login_user_get():
    return RedirectResponse(url="/login", status_code=303)

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if user:
        return RedirectResponse(url="/profile", status_code=303)
    return templates.TemplateResponse("auth/register.html", {"request": request})

@app.post("/api/register")
async def register_user(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
    db: Session = Depends(get_db),
):
    role = "student"

    if password != password_confirm:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Пароли не совпадают",
                "full_name": full_name,
                "email": email,
            },
            status_code=400,
        )

    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return templates.TemplateResponse(
            "auth/register.html",
            {
                "request": request,
                "error": "Пользователь с таким email уже существует",
                "full_name": full_name,
                "email": email,
            },
            status_code=400,
        )

    user = User(
        full_name=full_name.strip(),
        email=email.strip().lower(),
        password_hash=get_password_hash(password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id
    request.session["user_role"] = user.role
    request.session["user_name"] = user.full_name
    return RedirectResponse(url="/profile", status_code=303)

@app.get("/api/register")
async def register_user_get():
    return RedirectResponse(url="/register", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, db: Session = Depends(get_db)):
    user = get_current_user(request, db)
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    
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

    if user.role == "tutor":
        template = "profile/tutor.html"
    elif user.role == "admin":
        template = "profile/admin.html"
    else:
        template = "profile/student.html"

    return templates.TemplateResponse(template, {"request": request, "user": user})


@app.post("/api/profile/update")
async def update_profile(
    request: Request,
    full_name: str = Form(...),
    email: str = Form(...),
    db: Session = Depends(get_db),
):
    user_id = request.session.get("user_id")
    if not user_id:
        return RedirectResponse(url="/login", status_code=303)

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    new_full_name = (full_name or "").strip()
    new_email = (email or "").strip().lower()

    if not new_full_name:
        error = "Введите ФИО"
    elif not new_email or "@" not in new_email:
        error = "Введите корректный email"
    else:
        existing = (
            db.query(User)
            .filter(User.email == new_email, User.id != user.id)
            .first()
        )
        if existing:
            error = "Пользователь с таким email уже существует"
        else:
            error = None

    if error:
        if user.role == "tutor":
            template = "profile/tutor.html"
        elif user.role == "admin":
            template = "profile/admin.html"
        else:
            template = "profile/student.html"

        return templates.TemplateResponse(
            template,
            {"request": request, "user": user, "error": error},
            status_code=400,
        )

    user.full_name = new_full_name
    user.email = new_email
    db.commit()
    db.refresh(user)

    request.session["user_name"] = user.full_name
    return RedirectResponse(url="/profile", status_code=303)


@app.get("/api/profile/update")
async def update_profile_get():
    return RedirectResponse(url="/profile", status_code=303)

@app.get("/subjects", response_class=HTMLResponse)
async def subjects_page(request: Request):
    return templates.TemplateResponse("subjects.html", {"request": request})

@app.get("/support", response_class=HTMLResponse)
async def support_page(request: Request):
    return templates.TemplateResponse("support.html", {"request": request})

@app.get("/tutor-detail/{tutor_id}", response_class=HTMLResponse)
async def tutor_detail_page(request: Request, tutor_id: int, db: Session = Depends(get_db)):
    tutor = TUTORS.get(tutor_id)
    if not tutor:
        raise HTTPException(status_code=404, detail="Репетитор не найден")
    user = get_current_user(request, db)
    return templates.TemplateResponse(
        "tutor_detail.html",
        {"request": request, "tutor": tutor, "user": user},
    )

@app.get("/tutors", response_class=HTMLResponse)
async def tutors_page(request: Request):
    return templates.TemplateResponse("tutors.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)