from openai import OpenAI
import os, json
import logging

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def create_prompt_request(data):
    model_name = "gpt-4o-mini"
    system_prompt = """Sen bir beslenme uzmanısın. 
    Verilen yemeğin 100g başına besin değerlerini hesapla.
    SADECE aşağıdaki JSON formatında döndür, başka hiçbir şey yazma:
    {
        "portion_in_grams ": <sayı>,
        "carbs_per_100g": <sayı>,
        "sugar_per_100g": <sayı>,
        "oil_per_100g": <sayı>,
        "protein_per_100g": <sayı>,
        "salt_per_100g": <sayı>,
        "fibre_per_100g": <sayı>
    }
    Tüm değerler float olmalı. Null veya None kullanma."""

    message = f"Yemek: {data.meal_name}, Porsiyon: {data.portion}"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]
    try:
        response = client.chat.completions.create(
            messages=messages,
            model=model_name,
            response_format={"type": "json_object"},
        )

        prompt_result = json.loads(response.choices[0].message.content)
        return prompt_result

    except Exception as e:
        logger.error(f"OpenAI hatası: {str(e)}")
        return None
