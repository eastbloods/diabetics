from fastapi import APIRouter, Depends, HTTPException, Request
from openai import OpenAI
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from helper.open import create_prompt_request
from models import MealLog, Meal, Ingredient, MealIngredient
from schemas import MealAnalyzeRequest, MealAnalyzeResponse, MealLogResponse, MealLogHistoryResponse
from routers.auth import get_current_user
import os, json
from rate_limit import limiter
from cache import redis_client

router = APIRouter(prefix="/meal", tags=["meal"])


@router.post("/analyze", response_model=MealAnalyzeResponse)
@limiter.limit("10/minute")
def analyze_meal(request: Request, data: MealAnalyzeRequest, current_user=Depends(get_current_user)):
    parsed_response = create_prompt_request(data)
    if parsed_response is None:
        raise HTTPException(status_code=503, detail="AI servisi şu an kullanılamıyor.")

    analyze_response = MealAnalyzeResponse(
        meal_name=data.meal_name,
        portion=data.portion,
        total_carbs=parsed_response['carbs_per_100g'],
        total_sugar=parsed_response['sugar_per_100g'],
        total_oil=parsed_response['oil_per_100g'],
        total_protein=parsed_response['protein_per_100g'],
        total_salt=parsed_response['salt_per_100g'],
        total_fibre=parsed_response['fibre_per_100g']
    )
    return analyze_response


@router.post('/log', response_model=MealLogResponse)
@limiter.limit("20/minute")
def add_meal(request: Request, data: MealAnalyzeRequest, current_user=Depends(get_current_user),
             db: Session = Depends(get_db)):
    redis_query = redis_client.get(data.meal_name.lower().strip())
    print("Terminal'de var: ",redis_query)
    if redis_query:
        user_meal = MealLog(
            user_id=current_user.id,
            meal_id=int(redis_query),
            portion_multiplier=1
        )

        db.add(user_meal)
        db.commit()
        db.refresh(user_meal)
        return user_meal

    else:
        meal_query = db.query(Meal).filter(Meal.name == data.meal_name.lower().strip()).first()
        ingredient = db.query(Ingredient).filter(Ingredient.name == data.meal_name.lower().strip()).first()
        if meal_query and ingredient:
            user_meal = MealLog(
                user_id=current_user.id,
                meal_id=meal_query.id,
                portion_multiplier=1
            )

            db.add(user_meal)
            db.commit()
            db.refresh(user_meal)
            redis_client.set(f"{data.meal_name.lower().strip()}", f"{meal_query.id}")
            return user_meal
        else:
            parsed_response = create_prompt_request(data)
            if parsed_response is None:
                raise HTTPException(status_code=503, detail="AI servisi şu an kullanılamıyor.")

            try:
                db_add_meal = Meal(
                    name=data.meal_name.lower().strip()
                )
                db.add(db_add_meal)
                db.flush()

                lower_name = data.meal_name.lower().strip()
                db_add_ingredient = Ingredient(
                    name=lower_name,
                    carbs_per_100g=parsed_response['carbs_per_100g'],
                    sugar_per_100g=parsed_response['sugar_per_100g'],
                    oil_per_100g=parsed_response['oil_per_100g'],
                    protein_per_100g=parsed_response['protein_per_100g'],
                    salt_per_100g=parsed_response['salt_per_100g'],
                    fibre_per_100g=parsed_response['fibre_per_100g']
                )
                db.add(db_add_ingredient)
                db.flush()

                db_add_meal_ingredient = MealIngredient(
                    meal_id=db_add_meal.id,
                    ingredient_id=db_add_ingredient.id,
                    amount_grams=100,
                )
                db.add(db_add_meal_ingredient)
                db.flush()

                user_meal = MealLog(
                    user_id=current_user.id,
                    meal_id=db_add_meal.id,
                    portion_multiplier=parsed_response['portion_in_grams'] / 100
                )

                db.add(user_meal)
                db.commit()
                db.refresh(user_meal)

                redis_client.set(f"{lower_name}", f"{db_add_meal.id}")

                return user_meal
            except Exception as e:
                db.rollback()
                raise HTTPException(status_code=500, detail="Kayıt sırasında hata oluştu.")


@router.get("/history", response_model=List[MealLogHistoryResponse])
@limiter.limit("30/minute")
def get_meal_history(request: Request, limit: int = 10, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = (
        db.query(MealLog)
        .join(Meal, MealLog.meal_id == Meal.id)
        .filter(MealLog.user_id == current_user.id)
        .order_by(MealLog.logged_at.desc())
        .limit(limit)
        .all()
    )
    return [
        MealLogHistoryResponse(
            id=log.id,
            meal_name=log.meal.name,
            portion_multiplier=log.portion_multiplier,
            logged_at=log.logged_at
        )
        for log in logs
    ]
