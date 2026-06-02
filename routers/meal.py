from fastapi import APIRouter, Depends, HTTPException, Request
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

    # LLM'in tahmin ettiği porsiyonu kullan, yoksa 100g varsay
    portion_grams = float(parsed_response.get('portion_in_grams', 100))
    multiplier = portion_grams / 100

    analyze_response = MealAnalyzeResponse(
        meal_name=data.meal_name,
        portion=f"{portion_grams:.0f}g",
        total_carbs=round(parsed_response['carbs_per_100g'] * multiplier, 1),
        total_sugar=round(parsed_response['sugar_per_100g'] * multiplier, 1),
        total_oil=round(parsed_response['oil_per_100g'] * multiplier, 1),
        total_protein=round(parsed_response['protein_per_100g'] * multiplier, 1),
        total_salt=round(parsed_response['salt_per_100g'] * multiplier, 1),
        total_fibre=round(parsed_response['fibre_per_100g'] * multiplier, 1),
    )
    return analyze_response


@router.post('/log', response_model=MealLogResponse)
@limiter.limit("20/minute")
def add_meal(request: Request, data: MealAnalyzeRequest, current_user=Depends(get_current_user),
             db: Session = Depends(get_db)):
    redis_query = redis_client.get(data.meal_name.lower().strip())
    print("Terminal'de var: ", redis_query)
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
                portion_grams = float(parsed_response.get('portion_in_grams', 100))

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
                    portion_multiplier=portion_grams / 100
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


@router.get("/daily", response_model=dict)
@limiter.limit("30/minute")
def get_daily_totals(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """Bugünkü toplam besin değerlerini hesapla."""
    from datetime import date
    from sqlalchemy import cast, Date

    today_logs = (
        db.query(MealLog)
        .join(Meal, MealLog.meal_id == Meal.id)
        .filter(
            MealLog.user_id == current_user.id,
            cast(MealLog.logged_at, Date) == date.today()
        )
        .all()
    )

    totals = {
        "total_carbs": 0.0,
        "total_sugar": 0.0,
        "total_oil": 0.0,
        "total_protein": 0.0,
        "total_salt": 0.0,
        "total_fibre": 0.0,
        "meal_count": len(today_logs)
    }

    for log in today_logs:
        multiplier = float(log.portion_multiplier)
        for mi in log.meal.meal_ingredients:
            ing = mi.ingredient
            amount_multiplier = float(mi.amount_grams) / 100
            totals["total_carbs"] += float(ing.carbs_per_100g) * amount_multiplier * multiplier
            totals["total_sugar"] += float(ing.sugar_per_100g) * amount_multiplier * multiplier
            totals["total_oil"] += float(ing.oil_per_100g) * amount_multiplier * multiplier
            totals["total_protein"] += float(ing.protein_per_100g) * amount_multiplier * multiplier
            totals["total_salt"] += float(ing.salt_per_100g) * amount_multiplier * multiplier
            totals["total_fibre"] += float(ing.fibre_per_100g) * amount_multiplier * multiplier

    return {k: round(v, 1) if isinstance(v, float) else v for k, v in totals.items()}
