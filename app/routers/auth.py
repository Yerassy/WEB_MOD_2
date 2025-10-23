# app/routers/auth.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
import hashlib
import secrets
from datetime import datetime
from app.database import mongodb, run_async

router = APIRouter(prefix="/auth", tags=["auth"])

class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    name: str
    email: str
    role: str
    registration_date: datetime

def hash_password(password: str) -> str:
    """Simple password hashing using SHA-256 with salt"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}${password_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        salt, stored_hash = hashed_password.split('$')
        computed_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return secrets.compare_digest(computed_hash, stored_hash)
    except Exception:
        return False

@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate):
    def sync_register():
        collection = mongodb.get_collection("users")
        
        # Check if user already exists
        existing_user = collection.find_one({"email": user.email})
        if existing_user:
            raise ValueError("User with this email already exists")

        # Hash password
        hashed_password = hash_password(user.password)

        # Create new user
        new_user = {
            "name": user.name,
            "email": user.email,
            "password": hashed_password,
            "role": "user",
            "registration_date": datetime.utcnow()
        }

        # Insert user
        result = collection.insert_one(new_user)
        
        # Get the created user
        created_user = collection.find_one({"_id": result.inserted_id})
        return UserResponse(
            id=str(created_user["_id"]),
            name=created_user["name"],
            email=created_user["email"],
            role=created_user["role"],
            registration_date=created_user["registration_date"]
        )
    
    try:
        created_user = await run_async(sync_register)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/login")
async def login(user_data: UserLogin):
    def sync_login():
        collection = mongodb.get_collection("users")
        
        # Find user by email
        user = collection.find_one({"email": user_data.email})
        
        if not user or not verify_password(user_data.password, user["password"]):
            raise ValueError("Invalid credentials")
        
        return {
            "message": "Login successful",
            "user_id": str(user["_id"]),
            "email": user["email"],
            "name": user["name"]
        }
    
    try:
        result = await run_async(sync_login)
        return result
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")