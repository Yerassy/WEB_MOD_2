# app/main.py
from fastapi import FastAPI
from app.routers import users, auth  # Добавьте auth
from app.database import mongodb

app = FastAPI(title="MongoDB Users API", version="1.0.0")

# Connect to MongoDB on startup
@app.on_event("startup")
async def startup_event():
    mongodb.connect()

@app.on_event("shutdown")
async def shutdown_event():
    mongodb.close()

# Include routers
app.include_router(users.router)
app.include_router(auth.router)  # Добавьте эту строку

@app.get("/")
async def root():
    return {
        "message": "MongoDB User CRUD API", 
        "docs": "http://localhost:8000/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "database": "MongoDB"}