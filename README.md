# Herdwise farm health dashboard

A Flask + Vue dashboard for monitoring dairy-cow health. The live herd data is
read from Supabase; no database credentials or farm data are stored in this repo.

## Supabase setup

1. In the Supabase SQL Editor, run [supabase_schema.sql](supabase_schema.sql).
2. Add your cow records to the `public.cows` table. Put a public image URL in
   `image_url`, or use a site-local path such as `/static/images/daisy.jpg`.
3. Copy `.env.example` to `.env` locally and set `SUPABASE_URL` plus
   `SUPABASE_SECRET_KEY`. The secret key is server-only: never place it in Vue
   code, Git, or a public website.

The app reads the `cows` table by default. Set `SUPABASE_COWS_TABLE` if your
table has a different name. The table columns are the same as the detailed
parameter names shown in the interface. A JSONB `parameters` column is also
accepted for the sensor values if you already have that layout.

## Run locally

```powershell
python -m pip install -r requirements.txt
Copy-Item .env.example .env
# Add your real Supabase values to .env, then:
python app.py
```

Open `http://127.0.0.1:5000`. `GET /healthz` always returns plain-text `ok`
with status `200`, without querying Supabase.

## Deploy to Render

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and select the repository. Render will
   use [render.yaml](render.yaml) to create the web service.
3. Enter `SUPABASE_URL` and `SUPABASE_SECRET_KEY` when Render prompts for the
   secret environment variables, then deploy.
4. Use `https://your-service.onrender.com/healthz` for Render's health check or
   for an external cron request.

Render runs `gunicorn app:app` and automatically supplies the service port.
For manual setup, use build command `pip install -r requirements.txt`, start
command `gunicorn app:app`, and health-check path `/healthz`.
