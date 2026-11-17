# Jobs Matcher

Automated vacancy parser, AI analyzer and Telegram notifier.

Jobs Matcher collects fresh vacancies from job boards using each user's keywords, scores
every vacancy against the user's CV with an LLM, and sends the good matches to the user in
Telegram. Each message has inline buttons (**✅ Applied** / **🙈 Skip**) so the user can react.

## How it works

The pipeline runs as three chained Celery workers. Celery Beat starts it every
`PARSING_INTERVAL_HOURS` hours:

```
beat ──► [parsing] ──success──► [analysis] ──success──► [sending] ──► Telegram
```

| Worker       | Queue      | What it does                                                                                                   |
|--------------|------------|----------------------------------------------------------------------------------------------------------------|
| **Parsing**  | `parsing`  | Builds search queries from all unique user keywords, collects vacancy URLs and details from each source, and links the new vacancies to the users whose keywords found them. |
| **Analysis** | `analysis` | Parses and cleans each user's CV (PDF / DOCX / TXT). A cheap prefilter drops obvious mismatches, and the AI scores the rest from 0 to 100 with a short reasoning. |
| **Sending**  | `sending`  | Sends each vacancy whose score is at least the user's `min_score` to Telegram with the reaction buttons.       |

Each task is a small state machine (`START → … → COMPLETED`) whose runs are recorded in
`task_runs`. Every state works only on records it has not processed yet, so a crashed or
restarted run continues from where it stopped and never sends a vacancy twice.

### Vacancy lifecycle (per user)

```
NEW ─► REJECTED                               (prefilter, no AI call)
NEW ─► PENDING ─► SENT ─► APPLIED | SKIPPED   (user's reaction in Telegram)
```

`PENDING` means the AI has scored the vacancy. It is sent once its score reaches the user's
**current** `min_score`, so lowering the threshold needs no new analysis.

## Tech stack

- **Python 3.14** and **uv** for dependency management
- **Celery** with a **RabbitMQ** broker; **Flower** for monitoring
- **PostgreSQL** with **SQLAlchemy 2** (async, `asyncpg`) and **Alembic** migrations
- **pydantic-ai** for LLM calls (Gemini by default) and **pydantic / pydantic-settings**
- Scraping with **aiohttp**, **curl-cffi** and **Playwright** (stealth Chromium); **lxml** for HTML
- **pypdf** and **python-docx** for CV parsing
- **Docker** (multi-stage image) with per-service Compose files

## Project structure

```
app/
├── clients/              # external clients: AI (Gemini), Telegram
├── docker/               # Dockerfile, compose.yaml and services/*.yaml
├── infrastructure/
│   ├── database/         # engine, base CRUD, unit of work, Alembic migrations
│   └── source/           # scrapers (http / curl / browser) and source parsers (thejob API)
├── modules/
│   ├── analyzer/         # AI match analyzer, text cleaner, prefilter
│   ├── cv_parser/        # CV file → plain text
│   ├── data_extractor/   # per-source adapters → unified search / vacancy schemas
│   ├── domains/          # users, user_settings, vacancies, interactions, task runs
│   │                     #   (models, repositories, schemas, services)
│   ├── tasks/            # parsing / analysis / sending state machines + Telegram channels
│   └── workers/          # Celery app, routing, beat schedule, task entry points
└── shared/               # settings, enums, exceptions, logger, HTTP helpers
```

### Database tables

`users`, `user_settings`, `vacancies`, `vacancy_keywords`, `user_vacancy_interactions`,
`task_runs`.

## Configuration

All settings are read from a `.env` file in the project root (see
`app/shared/settings/__init__.py`).

```dotenv
# [project]
PROJECT_NAME=jobs-matcher
MODE=dev

# [sources]
DOU_URL=
DJINNI_URL=
THE_JOB_URL=
JOBICO_URL=

# [rabbit celery broker]
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=
RABBITMQ_PASSWORD=

# [postgresql-db]
POSTGRESQL_HOST=localhost
POSTGRESQL_PORT=5432
POSTGRESQL_USER=
POSTGRESQL_PASSWORD=
POSTGRESQL_DB=

# [ai tools]
AI_API_KEY=
AI_MODEL_NAME=

# [telegram]
TELEGRAM_BOT_TOKEN=
# optional service channels for task reports; an unset channel disables that task's messages
TELEGRAM_CHANNEL_PARSING=
TELEGRAM_CHANNEL_ANALYSIS=
TELEGRAM_CHANNEL_SENDING=

# [optional, defaults shown]
DEFAULT_MIN_SCORE=70.0        # 0..100, used when a user has no own threshold
CV_STORAGE_DIR=media/cvs      # uploaded CVs; must be shared by the bot and workers
PARSING_LOOKBACK_DAYS=30
PARSING_INTERVAL_HOURS=3
```

> Inside Docker, `POSTGRESQL_HOST`/`RABBITMQ_HOST` are overridden with the service names, so
> the same `.env` (with `localhost`) works both locally and in Compose.

## Running with Docker (recommended)

Run from the project root:

```bash
# full stack: postgres, rabbitmq, migrate, 3 workers, beat, flower
docker compose -f app/docker/compose.yaml up -d --build

# follow a worker's logs
docker compose -f app/docker/compose.yaml logs -f worker-parsing

# stop
docker compose -f app/docker/compose.yaml down
```

| Service            | Purpose                                                       |
|--------------------|---------------------------------------------------------------|
| `postgres`         | Database                                                      |
| `rabbitmq`         | Celery broker                                                 |
| `migrate`          | One-shot `alembic upgrade head`; the app services wait for it |
| `worker-parsing`   | Parsing queue (the `parser` image target, which includes Chromium) |
| `worker-analysis`  | Analysis queue                                                |
| `worker-sending`   | Sending queue                                                 |
| `beat`             | Scheduler that starts parsing every N hours                   |
| `flower`           | Celery monitoring at <http://127.0.0.1:5555>                  |

`media/` and the log files are bind-mounted, so the containers and a local run share them.

## Running locally

```bash
# 1. install dependencies (dev tools included)
uv sync
uv run playwright install chromium

# 2. start only the infrastructure in Docker
docker compose -f app/docker/compose.yaml up -d postgres rabbitmq

# 3. apply migrations
uv run alembic upgrade head

# 4. start the workers and the scheduler (each in its own terminal)
uv run celery -A app.modules.workers.jobs.tasks worker -Q parsing  -c 1 -n parsing@%h  -E
uv run celery -A app.modules.workers.jobs.tasks worker -Q analysis -c 1 -n analysis@%h -E
uv run celery -A app.modules.workers.jobs.tasks worker -Q sending  -c 1 -n sending@%h  -E
uv run celery -A app.modules.workers.jobs.tasks beat
```

To start a pipeline run by hand without waiting for beat:

```bash
uv run python -c "from app.modules.workers.jobs.tasks import parse_vacancies; parse_vacancies.delay()"
```

## Migrations

```bash
uv run alembic revision --autogenerate -m "describe change"
uv run alembic upgrade head
uv run alembic downgrade -1
```

## Development

```bash
uv run ruff check .        # lint
uv run ruff format .       # format
uv run mypy app            # strict type checking
uv run pytest              # tests (app/tests)
```

## Adding a new source

1. Add a parser or scraper under `app/infrastructure/source/` (API → `parser/api/sources/`;
   HTML/browser → `scraper/`).
2. Add a data-extractor adapter under `app/modules/data_extractor/adapters/<source>/` and the
   source extractors under `app/modules/data_extractor/sources/<source>/` that map the raw data
   to the shared `search` / `vacancy` schemas.
3. Add the source to the `VacancySource` enum (`app/shared/utils/enums/domains/vacancies/`)
   and register its extractor in `DataExtractorFactory.EXTRACTORS`
   (`app/modules/data_extractor/factory/`). The parsing worker picks it up automatically.

`thejob` is the reference implementation.
