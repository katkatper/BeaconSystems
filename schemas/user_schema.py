from pydantic import BaseModel, EmailStr

# SCHEMAS FOR USER CREATION, LOGIN, AND RESPONSE

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class AdminUserCreate(UserCreate):
    role: str = "investigator"
    agency_id: int | None = None


class UserLogin(BaseModel):
    username: str
    password: str


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class MfaEnable(BaseModel):
    code: str


class MfaLoginVerify(BaseModel):
    mfa_token: str
    code: str


class AdminPasswordReset(BaseModel):
    temporary_password: str


class UserResponse(BaseModel):
    user_id: int
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True

class UserRoleUpdate(BaseModel):
    role: str

