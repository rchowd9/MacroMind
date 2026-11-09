# MacroMind

MacroMind is a single-user calorie and macronutrient tracker. The Streamlit app is the user interface; Django provides a JSON API and stores foods, daily goals, and meal entries in SQLite.

Nutrition values are stored per 100 g and scaled by the logged serving size. The starter food library is for demonstration; verify values against the food labels you use.

## Run locally

Requires Python 3.10 or newer.

1. Create and activate a virtual environment, then install dependencies:

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install -r requirements.txt
   ```

2. Set the same API token in each terminal (choose your own long random value):

   ```powershell
   $env:MACROMIND_API_TOKEN = "replace-with-a-long-random-token"
   ```

3. In the first terminal, initialize and start Django:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

4. In a second terminal, set the same token and start Streamlit:

   ```powershell
   $env:MACROMIND_API_TOKEN = "replace-with-a-long-random-token"
   streamlit run app.py
   ```

The app is available at `http://localhost:8501`. For a different backend address, set `MACROMIND_API_URL`.

## Features

- Add foods with calories, protein, carbohydrates, and fat per 100 g.
- Log a gram-based portion for a selected day and remove entries.
- Set daily calorie and macro goals; view intake, remaining calories, and goal progress.
- Store data in Django's SQLite database.

## API

All API routes except the health check require `Authorization: Bearer <MACROMIND_API_TOKEN>`.

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/health/` | Backend health check |
| GET, POST | `/api/foods/` | List or add foods |
| GET, PUT | `/api/goal/` | Read or update the daily goal |
| GET, POST | `/api/meals/` | List meals (`?date=YYYY-MM-DD`) or log a meal |
| DELETE | `/api/meals/<id>/` | Remove a meal entry |

## Deployment

Deploy Django and Streamlit as separate services. Configure `MACROMIND_API_TOKEN` on both services with the same secret. On Streamlit, values may be set in the app's secrets, for example:

```toml
MACROMIND_API_URL = "https://your-backend.example.com"
MACROMIND_API_TOKEN = "your-long-random-token"
```

For Django, configure `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, `DJANGO_ALLOWED_HOSTS`, `MACROMIND_API_TOKEN`, and a persistent `MACROMIND_DATABASE` path. Run `python manage.py migrate` as a release/startup step, then serve `config.wsgi:application` with a production WSGI server (for example `gunicorn config.wsgi:application`). Streamlit should use `streamlit run app.py`. Put the backend behind HTTPS and use a managed persistent disk for its SQLite database; SQLite is intended for a single-user deployment, not concurrent multi-user hosting.

This initial version has one shared daily goal and food/meal library per deployment; it does not include user accounts or multi-user isolation.
