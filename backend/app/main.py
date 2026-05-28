# http://127.0.0.1:8000/docs ادرس سواگر 
# uvicorn app.main:app --reload برای اینمکه فست ای پی ای رو اجرا کنه 

from fastapi import FastAPI

app = FastAPI(
    title="ServiceDesk Radar API",
    version="1.0.0",
    description="Backend API for ServiceDesk Radar"
)

@app.get("/health")
def health_check():
    return {"status": "ok"}
