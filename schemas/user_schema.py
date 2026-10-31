from pydantic import BaseModel, ConfigDict, EmailStr, field_validator

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

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        username = value.strip()
        if not username:
            raise ValueError("Username is required")
        return username


class PasswordChange(BaseModel):
    current_password: str
    new_password: str


class MfaEnable(BaseModel):
    code: str


class MfaLoginVerify(BaseModel):
    mfa_token: str
    code: str


class MfaEnrollmentStart(BaseModel):
    mfa_token: str


class MfaEnrollmentComplete(MfaEnrollmentStart):
    code: str


class AdminPasswordReset(BaseModel):
    temporary_password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    username: str
    email: str
    role: str

class UserRoleUpdate(BaseModel):
    role: str

