from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime
from app.database import mongodb, run_async
from bson import ObjectId

router = APIRouter(prefix="/users", tags=["users"])

class UserCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    surname: str = Field(..., min_length=2, max_length=50)
    email: EmailStr

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=50)
    surname: Optional[str] = Field(None, min_length=2, max_length=50)
    email: Optional[EmailStr] = None

class UserResponse(BaseModel):
    id: str
    name: str
    surname: str
    email: str
    registration_date: datetime

# CREATE - Создать пользователя
@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate):
    def sync_create():
        collection = mongodb.get_collection("users")
        
        # Check if email already exists
        existing_user = collection.find_one({"email": user.email})
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Prepare user data
        user_data = user.dict()
        user_data["registration_date"] = datetime.utcnow()
        
        # Insert user
        result = collection.insert_one(user_data)
        
        # Get the created user
        created_user = collection.find_one({"_id": result.inserted_id})
        return UserResponse(
            id=str(created_user["_id"]),
            name=created_user["name"],
            surname=created_user["surname"],
            email=created_user["email"],
            registration_date=created_user["registration_date"]
        )
    
    try:
        created_user = await run_async(sync_create)
        return created_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# READ - Получить всех пользователей
@router.get("/", response_model=List[UserResponse])
async def get_all_users():
    def sync_get_all():
        collection = mongodb.get_collection("users")
        users = list(collection.find())
        result = []
        for user in users:
            result.append(UserResponse(
                id=str(user["_id"]),
                name=user["name"],
                surname=user["surname"],
                email=user["email"],
                registration_date=user["registration_date"]
            ))
        return result
    
    try:
        users = await run_async(sync_get_all)
        return users
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# READ - Получить пользователя по ID
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    def sync_get_by_id():
        collection = mongodb.get_collection("users")
        if not ObjectId.is_valid(user_id):
            return None
            
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(
                id=str(user["_id"]),
                name=user["name"],
                surname=user["surname"],
                email=user["email"],
                registration_date=user["registration_date"]
            )
        return None
    
    user = await run_async(sync_get_by_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# UPDATE - Обновить пользователя
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_update: UserUpdate):
    def sync_update():
        collection = mongodb.get_collection("users")
        if not ObjectId.is_valid(user_id):
            return None

        # Remove None values from update
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if not update_data:
            user = collection.find_one({"_id": ObjectId(user_id)})
            if user:
                return UserResponse(
                    id=str(user["_id"]),
                    name=user["name"],
                    surname=user["surname"],
                    email=user["email"],
                    registration_date=user["registration_date"]
                )
            return None
        
        # Check if email is being updated and if it already exists
        if user_update.email:
            existing_user = collection.find_one({
                "email": user_update.email,
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing_user:
                raise ValueError("User with this email already exists")

        collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        user = collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(
                id=str(user["_id"]),
                name=user["name"],
                surname=user["surname"],
                email=user["email"],
                registration_date=user["registration_date"]
            )
        return None
    
    try:
        updated_user = await run_async(sync_update)
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

# DELETE - Удалить пользователя
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: str):
    def sync_delete():
        collection = mongodb.get_collection("users")
        if not ObjectId.is_valid(user_id):
            return False
            
        result = collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0
    
    success = await run_async(sync_delete)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return None
