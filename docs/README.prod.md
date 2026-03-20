# Production Notes

This project is designed to run in a Dockerized environment with:

- FastAPI API (served by `uvicorn`)
- PostgreSQL database
- Redis for caching + JWT blacklist + Celery broker/results
- Celery worker/beat for background jobs (streaks, leaderboard updates, email reports)

## Required environment variables

The `.env.prod` file is expected to provide at least:

- `JWT_SECRET_KEY` (must be set to a strong value)
- SMTP settings if `EMAIL_ENABLED=true`
- `DATABASE_URL` and `REDIS_URL` if you deploy outside localhost

## Running

Use `docker-compose.prod.yml` with `--env-file .env.prod`, following the instructions in `README.md`.

