from decimal import Decimal
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    surname: str
    age: int
    diabetes_type: str
    height_cm: int
    weight_kg: Decimal = Field(max_digits=5, decimal_places=2)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    created_at: datetime

    class ConfigDict:
        from_attributes = True


class SugarLogCreate(BaseModel):
    sugar_rate: Decimal = Field(max_digits=5, decimal_places=1)
    starvation: bool


class SugarLogResponse(BaseModel):
    id: int
    sugar_rate: Decimal
    starvation: bool
    measure_at: datetime

    class ConfigDict:
        from_attributes = True


class InsulinLogCreate(BaseModel):
    insulin_type: str
    total_unit: int
    single_dose: int


class InsulinLogResponse(BaseModel):
    id: int
    insulin_type: str
    total_unit: int
    single_dose: int
    injected_at: datetime

    class ConfigDict:
        from_attributes = True


class MealAnalyzeRequest(BaseModel):
    meal_name: str
    portion: str


class MealAnalyzeResponse(BaseModel):
    meal_name: str
    portion: str
    total_carbs: float
    total_sugar: float
    total_oil: float
    total_protein: float
    total_salt: float
    total_fibre: float

    class ConfigDict:
        from_attributes = True


class MealLogResponse(BaseModel):
    id: int
    meal_id: int
    portion_multiplier: Decimal
    logged_at: datetime

    class ConfigDict:
        from_attributes = True


class MealLogHistoryResponse(BaseModel):
    id: int
    meal_name: str
    portion_multiplier: Decimal
    logged_at: datetime

    class ConfigDict:
        from_attributes = True