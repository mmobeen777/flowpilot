# FlowPilot

API gateway and usage metering SaaS built with Django REST Framework. Teams create API keys, track usage against quotas, and get billed monthly by Stripe based on actual call volume.

---

## Tech Stack

- **Backend** — Django 4, Django REST Framework
- **Auth** — JWT (simplejwt) + custom API key authentication
- **Database** — PostgreSQL 16
- **Cache / Broker** — Redis 7
- **Task Queue** — Celery + Celery Beat
- **Billing** — Stripe metered billing
- **Email** — Resend
- **Infrastructure** — Docker, Docker Compose, Nginx, Gunicorn

---

## Getting Started

### Prerequisites

- Docker
- Docker Compose

### 1. Clone the repo

```bash
git clone https://github.com/yourname/flowpilot.git
cd flowpilot
```

### 2. Set up environment variables


### 3. Start the stack

```bash
docker compose up --build
```

This starts 6 containers: `nginx`, `web` (Gunicorn), `db` (Postgres), `redis`, `worker` (Celery), and `beat` (Celery Beat).

On first boot, migrations run automatically and static files are collected.

### 4. Create a superuser

```bash
docker compose exec web python manage.py createsuperuser
```

---

## Project Structure

```
flowpilot/
├── docker-compose.yml
├── .env
├── nginx/
│   └── default.conf
└── backend/
    ├── Dockerfile
    ├── entrypoint.sh
    ├── requirements.txt
    ├── manage.py
    └── config/
    │   ├── settings/
    │   │   ├── base.py
    │   │   ├── dev.py
    │   │   └── prod.py
    │   ├── urls.py
    │   ├── wsgi.py
    │   └── celery.py
    └── apps/
        ├── user/       # User, Organisation, JWT auth
        ├── invitation/    # Invite flow
        ├── apikeys/        # API key model, custom auth backend
        ├── metering/       # Redis middleware, UsageRecord
        ├── billing/        # Plans, Subscriptions, Stripe sync
        └── utils/
                ├── core/    # core utils for project like permissions, custom error handling etc
                    ├── Counter.py
                    ├── ErrorHandling.py
                    ├── FlowPilotErrors.py
                    ├── Middleware.py
                    ├── Permissions.py
                    └── QueryLogger.py
                ├── Constants.py
                ├── Fields.py
                └── Models.py
                
            
```

---

## API Endpoints

### Auth

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/flowpilot/api/v1/users/register` | Create org + owner account |
| POST | `/flowpilot/api/v1/users/login` | Login, get JWT tokens |
| POST | `/flowpilot/api/v1/users/refresh-token` | Refresh access token |
| POST | `/flowpilot/api/v1/users/logout` | Blacklist refresh token |

### Invitations

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET / POST | `/flowpilot/api/v1/invitation` | List or send invitations (admin+) |
| POST | `/flowpilot/api/v1/invitation/accept` | Accept an invitation |
| GET | `/flowpilot/api/v1/invitation/retrieve/{id}` | Retrieve an invitation |

### API Keys

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET / POST | `/flowpilot/api/v1/key` | List or create API keys |
| DELETE | `/flowpilot/api/v1/key/{id}` | Revoke a key |
| POST | `/flowpilot/api/v1/key/{id}/rotate` | Rotate a key |
| GET | `/flowpilot/api/v1/key/verify` | Verify a key |

### Billing 

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flowpilot/api/v1/plans` | List available plans |
| POST | `/flowpilot/api/v1/subscriptions/` | Subscribe org to a plan |
| POST | `/flowpilot/api/v1/subscriptions/upgrade` | Upgrade or downgrade plan |
| POST | `/flowpilot/api/v1//webhooks/stripe` | Stripe event receiver |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/flowpilot/api/v1/analytics/usage/` | Call volume this month, by day |
| GET | `/flowpilot/api/v1/analytics/quota/` | Current usage vs plan limit |

---

## Environment Variables

```env
# Django
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Postgres
POSTGRES_DB=flowpilot
POSTGRES_USER=flowpilot
POSTGRES_PASSWORD=
POSTGRES_HOST=db
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/1

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

# Resend
RESEND_API_KEY=
```

---

## Common Commands

```bash
# Start all services
docker compose up

# Run in background
docker compose up -d

# Rebuild after requirements changes
docker compose up --build

# Run migrations
docker compose exec web python manage.py makemigrations
docker compose exec web python manage.py migrate

# Open Django shell
docker compose exec web python manage.py shell

# Run tests
docker compose exec web pytest

# Follow logs for a specific service
docker compose logs -f worker

# Full reset (deletes all data)
docker compose down -v
```

---

## How Usage Metering Works

Every authenticated API request passes through a custom DRF middleware that atomically increments a Redis counter keyed by org and billing month:

```
INCR org:{org_id}:calls:{YYYY-MM}
```

A nightly Celery Beat task reads each counter with `GETDEL` (atomic read + delete), reports the usage to Stripe as a metered billing record, and resets the counter cleanly. Stripe invoices the org at the end of the billing cycle based on total reported usage.

---

## Running Tests

```bash
docker compose exec web pytest
docker compose exec web pytest --cov=apps --cov-report=term-missing
```

---

## License

MIT
