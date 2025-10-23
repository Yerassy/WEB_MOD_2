from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
# Модель для создания пользователя
class UserCreate(BaseModel):
    name: str = Field(..., max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    role: str = "user"

# Модель для ответа (без пароля)
class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str

    class Config:
        orm_mode = True  # позволяет использовать объекты SQLAlchemy напрямую

class UserRead(BaseModel):
    id: int
    name: str
    email: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True
