# Diabetia

Diabetia is a personal health tracking API built for individuals managing diabetes. Users can log their meals with automatic nutritional analysis, track blood sugar measurements, and record insulin doses — all through a secure, token-based REST API.

Built with FastAPI for its async support and automatic OpenAPI documentation, Diabetia leverages non-blocking I/O to handle concurrent requests efficiently — particularly critical when querying the OpenAI API for nutritional data on unrecognized meals.

---

## Architecture

```
REST API (FastAPI) → PostgreSQL + Redis → OpenAI API
Deployed on AWS EC2 — accessible via https://healdiabet.space
```

Diabetia follows a cache-aside pattern for meal nutritional data. On each meal query, the system checks Redis first, then PostgreSQL, and only calls the OpenAI API if the meal is not found in either. This layered approach minimizes latency and reduces API costs — Redis operates in microseconds, PostgreSQL in milliseconds, and OpenAI in seconds.

**Stack**

- Runtime: Python 3.11
- Framework: FastAPI — async support, automatic OpenAPI documentation
- Database: PostgreSQL — relational data, Alembic migrations
- Cache: Redis — in-memory cache, cache-aside pattern
- Auth: JWT (python-jose) + bcrypt password hashing
- AI: OpenAI gpt-4o-mini — nutritional analysis for unrecognized meals
- Infrastructure: AWS EC2 (t3.micro), Docker Compose, nginx reverse proxy, Let's Encrypt SSL
- CI: GitHub Actions — automated test pipeline on every push

---

## Features

- User registration and login with JWT-based authentication
- Meal logging with automatic nutritional analysis — calories, carbohydrates, protein, and fat calculated per portion
- Nutritional data served from cache or database when available; OpenAI gpt-4o-mini queried only for unrecognized meals, results stored for future use
- Blood sugar measurement logging with timestamps
- Insulin dose logging with timestamps
- Rate limiting on all endpoints to prevent abuse

---

## Local Setup

**Prerequisites:** Docker, Docker Compose

1. Clone the repository

```bash
git clone https://github.com/username/diabetia.git
cd diabetia
```

2. Create a `.env` file in the project root

```
DATABASE_URL=postgresql://postgres:password@db:5432/diabetia
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=diabetia
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
```

3. Start the containers

```bash
docker compose up --build -d
```

4. Run database migrations

```bash
docker exec -it diabetics-api-1 alembic upgrade head
```

5. API is running at `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | /auth/register | No | Register a new user |
| POST | /auth/login | No | Login and receive JWT token |
| POST | /sugar/add | Yes | Log a blood sugar measurement |
| POST | /insulin/add | Yes | Log an insulin dose |
| POST | /meal/analyze | Yes | Analyze a meal by name, returns nutritional data |
| POST | /meal/log | Yes | Log a meal with portion size |

Full interactive documentation available at: https://healdiabet.space/docs

---

## Live Demo

API documentation: https://healdiabet.space/docs

---

## License

This project is for portfolio purposes only. All rights reserved.