from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI(
    title="TutorBook",
    version="0.1.0"
)

@app.get("/", response_class=HTMLResponse)
async def home():
    return 
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": ""}