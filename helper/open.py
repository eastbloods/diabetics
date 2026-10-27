from openai import OpenAI
import os
import json
import re
import logging

logger = logging.getLogger(__name__)

# Groq, OpenAI-compatible API sunar — sadece base_url ve key değişiyor
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

GROQ_PRIMARY_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_FALLBACK_MODEL = os.getenv("GROQ_FALLBACK_MODEL", "openai/gpt-oss-20b")
GROQ_MODEL_CHAIN = (GROQ_PRIMARY_MODEL, GROQ_FALLBACK_MODEL)


def _parse_json_object(raw_text: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw_text or "").strip(), flags=re.IGNORECASE)
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        cleaned = cleaned[start : end + 1]
    return json.loads(cleaned)


def create_prompt_request(data):
    system_prompt = """Sen bir beslenme uzmanısın. 
    Verilen yemeğin 100g başına besin değerlerini hesapla.
    SADECE aşağıdaki JSON formatında döndür, başka hiçbir şey yazma:
    {
        "portion_in_grams": <sayı>,
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

    for model_name in GROQ_MODEL_CHAIN:
        try:
            response = client.chat.completions.create(
                messages=messages,
                model=model_name,
                temperature=0.1,
                max_tokens=1024,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or ""
            return _parse_json_object(content)
        except Exception as e:
            logger.warning(f"Groq JSON mode hatası ({model_name}): {str(e)} — standart mod deneniyor")
            try:
                response = client.chat.completions.create(
                    messages=messages,
                    model=model_name,
                    temperature=0.1,
                    max_tokens=1024,
                )
                content = response.choices[0].message.content or ""
                return _parse_json_object(content)
            except Exception as inner_e:
                logger.error(f"Groq hatası ({model_name}): {str(inner_e)}")

    return None
