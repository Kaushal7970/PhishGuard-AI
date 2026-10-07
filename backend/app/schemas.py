from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RegisterRequest(Credentials):
    name: str = Field(min_length=1, max_length=120)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionRequest(BaseModel):
    url: HttpUrl


class PredictionResponse(BaseModel):
    id: int | None = None
    url: str
    prediction: str
    probability: float
    risk_score: float
    risk_level: str
    indicators: list[str]
    created_at: datetime | None = None


class ScanResponse(PredictionResponse):
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
