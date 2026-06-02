# Diabetia

Diabetia is a personal health tracking application built for individuals managing diabetes. Users can log meals with automatic AI-powered nutritional analysis, track blood sugar measurements, and record insulin doses — all through a clean web interface backed by a secure, token-based REST API.

---

## Architecture

```
Browser (Frontend) → nginx → FastAPI → PostgreSQL + Redis → Groq API (Llama 3.3 70B)
Deployed on AWS EC2 — accessible via https://healdiabet.space
```

Diabetia follows a **cache-aside pattern** for meal nutritional data. On each meal query, the system checks Redis first, then PostgreSQL, and only calls the Groq API if the meal is not found in either store. This layered approach minimizes latency and reduces API costs — Redis operates in microseconds, PostgreSQL in milliseconds, and Groq in seconds.

---

## Stack

| Layer | Technology |
|---|---|
| **Frontend** | Vanilla HTML/CSS/JavaScript — single-page app, dark theme, served via nginx |
| **Framework** | FastAPI — async support, automatic OpenAPI documentation |
| **Database** | PostgreSQL — relational data, Alembic migrations |
| **Cache** | Redis — in-memory cache-aside pattern |
| **Auth** | JWT (python-jose) + bcrypt password hashing |
| **AI** | Groq API (Llama 3.3 70B) — nutritional analysis for unrecognized meals |
| **Rate Limiting** | slowapi — per-IP request limits on all endpoints |
| **Infrastructure** | AWS EC2 (t3.micro), Docker Compose, nginx reverse proxy, Let's Encrypt SSL |
| **CI** | GitHub Actions — automated test pipeline on every push |

---

## Features

- User registration and login with JWT-based authentication
- Single-page frontend — login, register, and dashboard in one file, no framework
- Meal logging with automatic nutritional analysis — carbohydrates, sugar, protein, fat, fibre, and salt calculated per portion
- Cache-aside: Redis → PostgreSQL → Groq AI — only the slowest path (LLM) when needed
- Blood sugar measurement logging with real-time color feedback (normal / warning / high)
- Insulin dose logging by type (fast-acting, long-acting, mixed)
- Rate limiting on all endpoints to prevent abuse and control API costs

---

## Local Setup

**Prerequisites:** Docker, Docker Compose

1. Clone the repository

```bash
git clone https://github.com/eastbloods/diabetics.git
cd diabetics
```

2. Create a `.env` file in the project root

```
DATABASE_URL=postgresql://postgres:password@db:5432/diabetia
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=diabetia
SECRET_KEY=your_secret_key_here
GROQ_API_KEY=gsk_your_groq_api_key_here
```

3. Start all services

```bash
docker compose up --build -d
```

4. Run database migrations

```bash
docker exec -it diabetics-api-1 alembic upgrade head
```

5. Open the app at `http://localhost:8000` or API docs at `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register a new user |
| POST | /auth/login | No | Login and receive JWT token |
| POST | /sugar/add | Yes | Log a blood sugar measurement |
| POST | /insulin/add | Yes | Log an insulin dose |
| POST | /meal/analyze | Yes | Analyze a meal — returns nutritional values without saving |
| POST | /meal/log | Yes | Log a meal with portion size — saves to database |

Full interactive documentation: **https://healdiabet.space/docs**

---

## Design Decisions

**Why cache-aside for meals?**
Most users log the same meals repeatedly. Storing nutritional data after the first LLM lookup means subsequent requests skip the AI call entirely. Redis gives sub-millisecond lookups for hot meals; PostgreSQL handles cold cache misses; Groq only processes truly new meals.

**Why rate limiting on all endpoints?**
Each `/meal/analyze` or `/meal/log` request that hits the Groq API costs an external API call. Without limits, a single user running a script could exhaust rate limits or drive up costs.

**Why Groq (Llama 3.3 70B) instead of OpenAI?**
Free tier with comparable nutritional analysis quality for structured JSON output. The `response_format={"type": "json_object"}` parameter is supported, ensuring consistent parseable output without prompt engineering overhead.

---

## Live Demo

**Application:** https://healdiabet.space  
**API Documentation:** https://healdiabet.space/docs

---

## License

This project is for portfolio purposes only. All rights reserved.