<div align="center">

# 🎮 AI Game Maker

**Type a silly idea → get a finished, playable game in seconds.**

A full-stack web app that turns any simple game idea into a polished HTML5 game
with sound, particles, and high scores — using Google Gemini. Kids **create,
save to a shared community gallery, and play each other's games.** Built for
fun, engineered like a real product.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=streamlit&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)
![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F00?logo=sqlalchemy&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-8E75B2?logo=googlegemini&logoColor=white)
[![CI](https://github.com/Palak-eng/AI-GAME-GENERATOR/actions/workflows/ci.yml/badge.svg)](https://github.com/Palak-eng/AI-GAME-GENERATOR/actions/workflows/ci.yml)

</div>

---

## 🚀 What it does

- **Make a game** — type an idea ("cat jumps over dogs"), pick an art style, and
  get a complete, playable HTML5 game in ~30 seconds
- **Play instantly** — games run right in the browser
- **Save to your account** — keep your creations with a title
- **Share to the community gallery** — anyone can play the games you make
- **Play others' games** — browse the gallery and try what other kids built
- **Download** — grab any game as a single `game.html` to send to a friend
  (works on phones, no installs)

## 🏗️ Architecture

A clean **frontend / backend split**, built to be extended and deployed:

```
┌────────────────────────────┐   HTTP   ┌─────────────────────────────────────┐
│  Streamlit frontend        │ ───────► │  FastAPI REST backend (api)         │
│  (app.py)                  │   JSON   │  · User auth (bcrypt)               │
│  · Make / play games       │ ◄─────── │  · Session tokens                   │
│  · Login / signup          │          │  · Game CRUD + gallery              │
│  · Browse community gallery│          │  · Gemini game generation (POST /api/generate) │
└────────────────────────────┘          │  · SQLAlchemy → SQLite/Postgres     │
       UI layer                        └─────────────────────────────────────┘
                                              API + database + AI layer
```

**Where the AI runs:** game generation (Gemini) happens **on the FastAPI backend**
via `POST /api/generate`. The Streamlit frontend just sends the idea and gets
ready-to-play HTML back — so the Gemini key lives only on the backend, where it
belongs.

| Layer | Tech | File |
|---|---|---|
| Frontend | Streamlit | `app.py` |
| API | FastAPI | `api.py` |
| DB models | SQLAlchemy ORM | `api.py` |
| Auth | bcrypt + session tokens | `api.py` |
| API client | `requests` | `apiclient.py` |
| AI pipeline | Google Gemini | `generator.py` |
| Curated game templates | Hand-built base games | `templates.py` |

**How game quality stays consistent:** instead of only letting the LLM invent a
game from scratch, matching ideas are RESKINNED from hand-built, phone+PC-tested
base templates in `templates.py` (runner, collector). Gemini rewrites the theme,
colors, and characters while the proven game logic stays intact — then a
self-review pass fixes any residual bugs. Unmatched ideas still generate fully
from scratch.

### Why a real backend?

This is what takes the project from *demo* to *product*: real user accounts,
a database, a documented REST API, and a shared multiuser gallery — the same
patterns used in production SaaS apps.

---

## 🚀 Run it locally

### 1. Get a free API key
Grab one at **[Google AI Studio](https://aistudio.google.com/apikey)** (free).

### 2. Install

```bash
git clone https://github.com/Palak-eng/AI-GAME-GENERATOR.git
cd AI-GAME-GENERATOR
pip install -r requirements.txt
```

### 3. Add your key

```bash
copy .env.example .env
```

Edit `.env` and replace `your_key_here`:

```
GEMINI_API_KEY=AIzaSyYourActualKeyHere
```

### 4. Start the backend API (does the AI generation)

```bash
uvicorn api:app --port 8000
```

### 5. Start the frontend app

In a second terminal:

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`), create an
account, and start making games!

> The frontend talks to the API at `http://localhost:8000`. If your API lives
> elsewhere, set the `API_BASE_URL` env var:
> `export API_BASE_URL=https://your-api-url` (or use a `.env` line `API_BASE_URL=...`).

---

## 🌍 Deploy it free online

Two free services, connected by the `API_BASE_URL`:

| Service | Hosts | Where |
|---|---|---|
| FastAPI backend + AI | [Render](https://render.com) (free web service) | `GEMINI_API_KEY` + optional `DATABASE_URL` |
| Streamlit frontend | [Streamlit Community Cloud](https://share.streamlit.io) | `API_BASE_URL` only |

### Backend → Render

1. Push this repo to GitHub.
2. On Render, **New → Web Service** → connect the repo.
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn api:app --host 0.0.0.0 --port 10000`
   - Plan: Free
3. Environment: add `GEMINI_API_KEY=...`
4. **For persistent accounts/games** (SQLite is wiped on free-tier restarts):
   add a free **Postgres** database on Render and set `DATABASE_URL` to its
   internal connection string. The app reads it automatically — no code change.
5. Verify: open `https://your-api.onrender.com/health` → `{"status":"ok"}`.

> One-click option: this repo includes a `render.yaml` blueprint. On Render,
> **New → Blueprint** and point it at the repo to provision the web service
> **and** Postgres together. Set `GEMINI_API_KEY` as an env var after.

### Frontend → Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** →
   your repo → main file `app.py` → **Deploy**.
2. **Settings → Secrets**, add exactly:
   ```toml
   API_BASE_URL = "https://your-api.onrender.com"
   ```
   (The Gemini key is **not** needed here — generation runs on the backend.)

---

## 🧪 CI / Development

GitHub Actions runs on every push: **ruff lint**, **format check**, and
**pytest** (39 tests covering the AI pipeline incl. the template engine + full
API incl. auth, gallery, and game generation).

```bash
pip install -e ".[dev]"

ruff check .          # lint
ruff format .         # format
pytest                # tests
```

## 📦 Project structure

```
AI-GAME-GENERATOR/
├── app.py                 # Streamlit frontend + gallery UI
├── api.py                 # FastAPI backend: auth, games, gallery
├── apiclient.py           # Small HTTP client for the UI → API
├── generator.py           # AI pipeline: design → code → validate → fix
├── templates.py           # Hand-built, phone+PC-tested base-game templates
├── gen_features.py        # Frontend helpers
├── requirements.txt       # Runtime dependencies
├── pyproject.toml         # Lint/test config
├── .env.example           # API key template
├── .streamlit/            # Theme config
├── .github/workflows/     # CI
├── render.yaml            # Render blueprint (web service + Postgres)
└── tests/                 # 39 unit/API tests
```

## 📄 License

MIT. Make games, share games, have fun! 🕹️
