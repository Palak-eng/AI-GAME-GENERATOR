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
[![CI](https://github.com/YOUR_USER/YOUR_REPO/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USER/YOUR_REPO/actions/workflows/ci.yml)

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
┌────────────────────────────┐        ┌─────────────────────────────┐
│  Streamlit frontend        │  HTTP  │  FastAPI REST backend (api) │
│  (app.py)                  │ ─────► │  · User auth (bcrypt)       │
│  · Make / play games       │  JSON  │  · Session tokens           │
│  · Login / signup          │ ◄───── │  · Game CRUD + gallery      │
│  · Browse community gallery│        │  · SQLAlchemy → SQLite/Postgres │
└────────────────────────────┘        └─────────────────────────────┘
       UI layer                          API + database layer
```

| Layer | Tech | File |
|---|---|---|
| Frontend | Streamlit | `app.py` |
| API | FastAPI | `api.py` |
| DB models | SQLAlchemy ORM | `api.py` |
| Auth | bcrypt + session tokens | `api.py` |
| API client | `requests` | `apiclient.py` |
| AI pipeline | Google Gemini | `generator.py` |

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
git clone <your-repo-url>
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

### 4. Start the backend API

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

### Option A: Everything on Render (recommended, database-backed)

1. Push this repo to GitHub.
2. On [Render.com](https://render.com), create a **Web Service** for the API:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn api:app --host 0.0.0.0 --port 10000`
   - Set an env var `GEMINI_API_KEY=...`
   - (Optional) add a free Postgres and set `DATABASE_URL=...`
3. Create a **Static Site** (or second web service) for the frontend, or run the
   Streamlit app on **Streamlit Community Cloud** pointing at `app.py`, and set
   the `API_BASE_URL` secret to your Render API URL.

### Option B: Streamlit Community Cloud (frontend only)

1. Push this repo to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) → **Create app** →
   your repo → main file `app.py` → **Deploy**.
3. Add your key under **Settings → Secrets**: `GEMINI_API_KEY=...`
4. Note: for the *gallery* to work, the FastAPI backend must also be deployed
   and `API_BASE_URL` pointed at it.

---

## 🧪 CI / Development

GitHub Actions runs on every push: **ruff lint**, **format check**, and
**pytest** (28 tests covering the AI pipeline + full API incl. auth & gallery).

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
├── gen_features.py        # Frontend helpers
├── requirements.txt       # Runtime dependencies
├── pyproject.toml         # Lint/test config
├── .env.example           # API key template
├── .streamlit/            # Theme config
├── .github/workflows/     # CI
└── tests/                 # 28 unit/API tests
```

## 📄 License

MIT. Make games, share games, have fun! 🕹️
