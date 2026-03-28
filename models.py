from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    surname = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    height_cm = Column(Integer, nullable=False)
    weight_kg = Column(DECIMAL(5, 2), nullable=False)
    diabetes_type = Column(String(25), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    # İlişkiler
    meal_logs = relationship("MealLog", back_populates="user")
    sugar_logs = relationship("SugarLog", back_populates="user")
    insulin_logs = relationship("InsulinLog", back_populates="user")


class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)

    meal_logs = relationship("MealLog", back_populates="meal")
    meal_ingredients = relationship("MealIngredient", back_populates="meal")


class MealLog(Base):
    __tablename__ = "meal_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    meal_id = Column(Integer, ForeignKey('meals.id'))
    portion_multiplier = Column(DECIMAL(4, 2), nullable=False)
    logged_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="meal_logs")
    meal = relationship("Meal", back_populates="meal_logs")


class MealIngredient(Base):
    __tablename__ = "meal_ingredients"

    meal_id = Column(Integer, ForeignKey('meals.id'), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey('ingredients.id'), primary_key=True)
    amount_grams = Column(DECIMAL(6, 2), nullable=False)

    meal = relationship("Meal", back_populates="meal_ingredients")
    ingredient = relationship("Ingredient", back_populates="meal_ingredients")


class Ingredient(Base):
    __tablename__ = "ingredients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    carbs_per_100g = Column(DECIMAL(6, 2), nullable=False)
    sugar_per_100g = Column(DECIMAL(6, 2), nullable=False)
    oil_per_100g = Column(DECIMAL(6, 2), nullable=False)
    protein_per_100g = Column(DECIMAL(6, 2), nullable=False)
    salt_per_100g = Column(DECIMAL(6, 2), nullable=False)
    fibre_per_100g = Column(DECIMAL(6, 2), nullable=False)

    meal_ingredients = relationship("MealIngredient", back_populates="ingredient")


class SugarLog(Base):
    __tablename__ = "sugar_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    sugar_rate = Column(DECIMAL(5, 1), nullable=False)
    starvation = Column(Boolean, nullable=False)
    measure_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="sugar_logs")


class InsulinLog(Base):
    __tablename__ = "insulin_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    insulin_type = Column(String, nullable=False)
    total_unit = Column(Integer, nullable=False)
    single_dose = Column(Integer, nullable=False)
    injected_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="insulin_logs")


