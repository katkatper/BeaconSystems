from pydantic import BaseModel, EmailStr

# SCHEMAS FOR USER CREATION, LOGIN, AND RESPONSE

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role: str

