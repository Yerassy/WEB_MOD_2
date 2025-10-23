# app/crud.py
from bson import ObjectId
from typing import List, Optional
from app.models import UserCreate, UserUpdate, UserInDB, UserResponse
from app.database import get_database

class UserCRUD:
    def __init__(self):
        self.collection_name = "users"

    async def get_collection(self):
        database = await get_database()
        return database[self.collection_name]

    async def create_user(self, user: UserCreate) -> UserInDB:
        collection = await self.get_collection()
        
        # Check if email already exists
        existing_user = await collection.find_one({"email": user.email})
        if existing_user:
            raise ValueError("User with this email already exists")
        
        user_data = UserInDB(**user.dict())
        result = await collection.insert_one(user_data.dict(by_alias=True))
        
        # Get the created user
        created_user = await collection.find_one({"_id": result.inserted_id})
        return UserInDB(**created_user)

    async def get_all_users(self) -> List[UserResponse]:
        collection = await self.get_collection()
        users = await collection.find().to_list(length=1000)
        return [UserResponse(**user) for user in users]

    async def get_user_by_id(self, user_id: str) -> Optional[UserResponse]:
        collection = await self.get_collection()
        if not ObjectId.is_valid(user_id):
            return None
            
        user = await collection.find_one({"_id": ObjectId(user_id)})
        if user:
            return UserResponse(**user)
        return None

    async def update_user(self, user_id: str, user_update: UserUpdate) -> Optional[UserResponse]:
        collection = await self.get_collection()
        if not ObjectId.is_valid(user_id):
            return None

        # Remove None values from update
        update_data = {k: v for k, v in user_update.dict().items() if v is not None}
        
        if not update_data:
            return await self.get_user_by_id(user_id)
        
        # Check if email is being updated and if it already exists
        if user_update.email:
            existing_user = await collection.find_one({
                "email": user_update.email,
                "_id": {"$ne": ObjectId(user_id)}
            })
            if existing_user:
                raise ValueError("User with this email already exists")

        await collection.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        
        return await self.get_user_by_id(user_id)

    async def delete_user(self, user_id: str) -> bool:
        collection = await self.get_collection()
        if not ObjectId.is_valid(user_id):
            return False
            
        result = await collection.delete_one({"_id": ObjectId(user_id)})
        return result.deleted_count > 0

# Create global instance
user_crud = UserCRUD()