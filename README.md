# 🏓 PingPulse — Website Health Monitor

## What is PingPulse? 

Imagine you have a toy robot. You tell the robot: *"Hey, every minute, go knock on my friend's door and check if they answer."*

If the friend answers — great! The robot writes down **"UP ✅"**.
If nobody answers — the robot writes down **"DOWN ❌"** and notes what went wrong.

**PingPulse is that robot — but for websites.**

You give it a list of website addresses (URLs). Every minute, it visits each one and checks:
- Did the website respond?
- Did it respond fast enough?
- Did it give the right answer (status code 200 = "I'm alive!")?

All results are saved so you can look back and see the history of your website's health.

---

## The Big Picture — How Everything Flows

```
You (Admin)
    |
    | Add a website to monitor via Django Admin Panel
    v
[Database - PostgreSQL]  <-- stores Monitor info & HeartbeatLogs
    ^
    |
[Celery Beat] -- every 60 seconds --> [Celery Worker]
                                            |
                                            | ping_all_monitors task
                                            |   loops through all active monitors
                                            |
                                            | ping_monitor task (one per website)
                                            |   visits the URL
                                            |   records response time & status
                                            v
                                    [HeartbeatLog saved to DB]
```

**In plain English:**
1. You add a website (e.g. `https://google.com`) via the admin panel.
2. Every 60 seconds, Celery Beat wakes up and says *"time to check!"*
3. It fires off a task to the Celery Worker.
4. The Worker visits every active website, measures how fast it responds, and saves the result.
5. You can see all results in the Django Admin panel.

---

## Project Structure

```
PingPulse/
├── apps/
│   └── monitors/           ← The heart of the app
│       ├── migrations/     ← Database setup instructions
│       ├── models.py       ← What data we store
│       ├── tasks.py        ← The robot that pings websites
│       ├── admin.py        ← What you see in the admin panel
│       ├── views.py        ← (Future: web pages/API)
│       └── apps.py         ← App registration config
├── config/
│   ├── settings.py         ← Master control panel
│   ├── urls.py             ← URL routing
│   ├── celery.py           ← Celery startup config
│   ├── wsgi.py             ← Production web server entry
│   └── asgi.py             ← Async web server entry
├── .env                    ← Secret passwords & config
├── requirements.txt        ← List of libraries to install
├── Dockerfile              ← Recipe to build the app container
├── docker-compose.yml      ← Runs all services together
└── manage.py               ← Django's command-line tool
```

---

## File-by-File Breakdown

### `apps/monitors/models.py` — The Data Blueprint
**Why it exists:** Defines the shape of data stored in the database.

**Monitor** — Represents one website you want to watch:
| Field | What it stores |
|---|---|
| `user` | Which user owns this monitor |
| `name` | A friendly name like "My Blog" |
| `url` | The website address to ping |
| `interval_seconds` | How often to check (default: 60s) |
| `expected_status_code` | What a healthy response looks like (default: 200) |
| `timeout_seconds` | How long to wait before giving up (default: 5s) |
| `status` | Current state: UP / DOWN / PENDING |
| `is_active` | Whether this monitor is running or paused |
| `last_checked_at` | Timestamp of the last ping |

**HeartbeatLog** — One record per ping attempt:
| Field | What it stores |
|---|---|
| `monitor` | Which website this log belongs to |
| `status_code` | HTTP code returned (200, 404, 500, etc.) |
| `response_time_ms` | How many milliseconds the site took to respond |
| `is_successful` | True/False — did it match the expected status? |
| `error_message` | What went wrong (if anything) |
| `checked_at` | When this ping happened |

---

### `apps/monitors/tasks.py` — The Robot Worker
**Why it exists:** Contains the actual logic that visits websites and records results. These are background jobs — they run automatically, not when a user clicks something.

**`ping_monitor(monitor_id)`**
- Fetches one Monitor from the database
- Sends an HTTP request to its URL using Python's built-in `urllib`
- Measures response time in milliseconds
- Compares the returned status code to `expected_status_code`
- Updates the Monitor's status (UP/DOWN)
- Saves a new HeartbeatLog entry

**`ping_all_monitors()`**
- Fetches all active monitors
- Calls `ping_monitor.delay(id)` for each one — `.delay()` means "run this in the background, don't wait"
- This is the task that Celery Beat triggers every 60 seconds

---

### `apps/monitors/admin.py` — The Control Dashboard
**Why it exists:** Registers models with Django's built-in admin panel so you can manage data through a web UI without writing any extra code.

- **MonitorAdmin** — Shows name, URL, status, interval, last checked time, and active state. Filterable by status and active state.
- **HeartbeatLogAdmin** — Shows each ping result. Read-only `checked_at` field since it's auto-set.

Access it at: `http://localhost:8000/admin/`

---

### `apps/monitors/migrations/0001_initial.py` — Database Setup Script
**Why it exists:** Django auto-generates this file when you run `makemigrations`. It tells the database *"create these tables with these columns."* You never edit this by hand — Django manages it.

---

### `apps/monitors/views.py` — Web Pages / API (Placeholder)
**Why it exists:** This is where you'll add API endpoints or web pages in the future (e.g., a dashboard showing monitor statuses). Currently empty — the admin panel handles everything for now.

---

### `config/settings.py` — Master Control Panel
**Why it exists:** The single file that configures the entire Django project.

Key sections:
- **INSTALLED_APPS** — Lists all active apps including `apps.monitors`
- **DATABASES** — Connects to PostgreSQL using the `DATABASE_URL` from `.env`
- **CELERY_BROKER_URL / CELERY_RESULT_BACKEND** — Points Celery to Redis
- **CELERY_BEAT_SCHEDULE** — Schedules `ping_all_monitors` to run every 60 seconds

---

### `config/celery.py` — Celery Startup Config
**Why it exists:** Initializes the Celery application and tells it to use Django's settings (anything prefixed with `CELERY_`). Also calls `autodiscover_tasks()` so Celery automatically finds task files in all installed apps.

---

### `config/urls.py` — URL Router
**Why it exists:** Maps URL paths to views. Currently only has the admin panel route (`/admin/`). Future API routes will be added here.

---

### `config/wsgi.py` & `config/asgi.py` — Web Server Entry Points
**Why they exist:** These are the standard entry points for deploying Django. `wsgi.py` is for traditional servers (Gunicorn), `asgi.py` is for async servers. Docker uses `wsgi.py` via Gunicorn in production.

---

### `requirements.txt` — Library Shopping List
**Why it exists:** Lists every Python package the project needs. Run `pip install -r requirements.txt` to install them all.

| Library | Why it's installed |
|---|---|
| `Django` | The web framework — handles routing, ORM, admin, auth |
| `djangorestframework` | Adds tools to build REST APIs (for future API endpoints) |
| `celery` | The background task queue — runs jobs outside of web requests |
| `redis` | Python client to talk to Redis (Celery's message broker) |
| `django-celery-beat` | Stores Celery's periodic schedules in the database |
| `psycopg2-binary` | Python driver to connect Django to PostgreSQL |
| `django-environ` | Reads `.env` files and injects values into Django settings |
| `httpx` | A modern HTTP client (available for future use in tasks) |
| `whitenoise` | Serves static files (CSS/JS) directly from Django in production |
| `gunicorn` | Production-grade web server that runs the Django app |

---

### `Dockerfile` — App Container Recipe
**Why it exists:** Tells Docker how to build a container image for the app.

Steps it performs:
1. Starts from a slim Python 3.11 image
2. Installs system dependencies needed for PostgreSQL (`libpq-dev`)
3. Copies and installs `requirements.txt`
4. Copies the entire project into `/app`
5. Exposes port 8000

---

### `docker-compose.yml` — Runs Everything Together
**Why it exists:** Defines and connects all 5 services needed to run PingPulse locally with one command (`docker-compose up`).

| Service | What it does |
|---|---|
| `db` | PostgreSQL database — stores all monitors and logs |
| `redis` | Redis — acts as the message broker between Beat and Worker |
| `web` | Django app — serves the admin panel on port 8000 |
| `celery_worker` | Listens for tasks and executes them (does the actual pinging) |
| `celery_beat` | The scheduler — fires `ping_all_monitors` every 60 seconds |

---

### `manage.py` — Django's Swiss Army Knife
**Why it exists:** Django's command-line utility. Used to run the server, create migrations, create superusers, open a shell, etc.

Common commands:
```bash
python manage.py runserver        # Start dev server
python manage.py makemigrations   # Generate migration files
python manage.py migrate          # Apply migrations to DB
python manage.py createsuperuser  # Create an admin user
```

---

## How to Run the Project

### Prerequisites
- Docker & Docker Compose installed

### Steps

```bash
# 1. Clone the project
git clone <repo-url>
cd PingPulse

# 2. Start all services
docker-compose up --build

# 3. In a new terminal, apply database migrations
docker-compose exec web python manage.py migrate

# 4. Create an admin user
docker-compose exec web python manage.py createsuperuser

# 5. Open the admin panel
# Visit: http://localhost:8000/admin/
# Log in and add a Monitor (e.g. name="Google", url="https://google.com")
# Wait 60 seconds and check HeartbeatLogs to see results!
```

---

## The Full Story in One Paragraph

PingPulse is a website uptime monitor built with Django, Celery, Redis, and PostgreSQL, all running inside Docker. You add websites to watch via the Django admin panel — each website becomes a `Monitor` record in the database. Every 60 seconds, Celery Beat (the scheduler) triggers the `ping_all_monitors` task. The Celery Worker picks it up, loops through every active monitor, visits each URL using Python's `urllib`, measures the response time, checks if the status code matches what's expected, and saves the result as a `HeartbeatLog` in the database. The Monitor's status is updated to UP or DOWN. You can view all of this history in the admin panel. The whole system runs as 5 Docker containers talking to each other — the web app, the database, Redis, the task worker, and the scheduler.
