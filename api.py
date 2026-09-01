"""
REST API backend for the AI Game Maker.

Provides user accounts (register/login) and a shared game gallery via FastAPI.
Exposed as `app` for uvicorn, and also usable by the Streamlit frontend
through `http://localhost:8000` (or any configured API_BASE_URL).

Storage: SQLite via SQLAlchemy. Swap `DATABASE_URL` env var to use Postgres
in production (e.g. on Render/Railway).

Auth: passwords hashed with bcrypt; clients get an opaque session token stored
server-side. Token is sent via the `Authorization: Bearer <token>` header.
"""

import os
import secrets
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, Header, HTTPException
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, relationship, sessionmaker

from generator import GameGenerationError, generate_game

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gamelab.db")


def _normalize_database_url(url: str) -> str:
    """Ensure SQLAlchemy uses the psycopg3 driver for Postgres URLs.

    Render/Railway hand out "postgresql://..." URLs, but SQLAlchemy needs an
    explicit driver dialect (postgresql+psycopg) to pick psycopg3.
    """
    if url.startswith("postgresql://") and "+" not in url.split("://")[0]:
        return "postgresql+psycopg://" + url.split("://", 1)[1]
    return url


DATABASE_URL = _normalize_database_url(DATABASE_URL)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app = FastAPI(title="AI Game Maker API")


# ─── Database models ─────────────────────────────────────────────────────────


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    games = relationship("Game", back_populates="owner")


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True)
    title = Column(String(120), nullable=False)
    idea = Column(String(500), default="")
    style = Column(String(50), default="arcade")
    code = Column(Text, nullable=False)
    is_public = Column(Integer, default=1)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="games")


class SessionToken(Base):
    __tablename__ = "session_tokens"

    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


Base.metadata.create_all(bind=engine)


# ─── Pydantic schemas ────────────────────────────────────────────────────────


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class GameCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    idea: str = ""
    style: str = "arcade"
    code: str = Field(min_length=20)
    is_public: int = 1


class GameUpdate(BaseModel):
    is_public: int | None = None
    title: str | None = None


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=500)
    style: str = "arcade"


# ─── Helpers ─────────────────────────────────────────────────────────────────


def _db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _hash_password(password: str) -> str:
    return pwd_context.hash(password)


def _verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def _get_current_user(authorization: str = Header(None), db: Session = Depends(_db)) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = authorization.split(" ", 1)[1].strip()
    row = db.query(SessionToken).filter(SessionToken.token == token).first()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == row.user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def _game_to_dict(game: Game) -> dict:
    return {
        "id": game.id,
        "title": game.title,
        "idea": game.idea,
        "style": game.style,
        "is_public": bool(game.is_public),
        "created_at": game.created_at.isoformat() if game.created_at else None,
        "owner": game.owner.username if game.owner else "anonymous",
    }


# ─── Auth endpoints ──────────────────────────────────────────────────────────


@app.post("/api/register", status_code=201)
def register(req: RegisterRequest, db: Session = Depends(_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=409, detail="Username already taken")
    user = User(username=req.username, password_hash=_hash_password(req.password))
    db.add(user)
    db.commit()
    token = secrets.token_hex(32)
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()
    return {"token": token, "username": user.username, "id": user.id}


@app.post("/api/login")
def login(req: LoginRequest, db: Session = Depends(_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not _verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    token = secrets.token_hex(32)
    db.add(SessionToken(token=token, user_id=user.id))
    db.commit()
    return {"token": token, "username": user.username, "id": user.id}


@app.post("/api/logout")
def logout(
    user: User = Depends(_get_current_user),
    authorization: str = Header(None),
    db: Session = Depends(_db),
):
    token = authorization.split(" ", 1)[1].strip()
    db.query(SessionToken).filter(SessionToken.token == token).delete()
    db.commit()
    return {"ok": True}


@app.get("/api/me")
def me(user: User = Depends(_get_current_user)):
    return {"id": user.id, "username": user.username}


# ─── Game endpoints ──────────────────────────────────────────────────────────


@app.post("/api/games", status_code=201)
def create_game(
    payload: GameCreate, user: User = Depends(_get_current_user), db: Session = Depends(_db)
):
    game = Game(
        title=payload.title,
        idea=payload.idea,
        style=payload.style,
        code=payload.code,
        is_public=payload.is_public,
        owner_id=user.id,
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return {"id": game.id, **_game_to_dict(game)}


@app.get("/api/games")
def list_games(
    mine: bool = False, user: User = Depends(_get_current_user), db: Session = Depends(_db)
):
    q = db.query(Game)
    q = q.filter(Game.owner_id == user.id) if mine else q.filter(Game.is_public == 1)
    games = q.order_by(Game.created_at.desc()).all()
    return [_game_to_dict(g) for g in games]


@app.get("/api/games/{game_id}")
def get_game(game_id: int, db: Session = Depends(_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    if not game.is_public:
        raise HTTPException(status_code=403, detail="Game is private")
    data = _game_to_dict(game)
    data["code"] = game.code
    return data


@app.patch("/api/games/{game_id}")
def update_game(
    game_id: int,
    payload: GameUpdate,
    user: User = Depends(_get_current_user),
    db: Session = Depends(_db),
):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game or game.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Game not found")
    if payload.title is not None:
        game.title = payload.title
    if payload.is_public is not None:
        game.is_public = payload.is_public
    db.commit()
    return _game_to_dict(game)


@app.delete("/api/games/{game_id}", status_code=204)
def delete_game(game_id: int, user: User = Depends(_get_current_user), db: Session = Depends(_db)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game or game.owner_id != user.id:
        raise HTTPException(status_code=404, detail="Game not found")
    db.delete(game)
    db.commit()


@app.post("/api/generate")
def generate(req: GenerateRequest):
    """Generate a playable HTML5 game from a text idea.

    The heavy AI work (Gemini) runs here on the backend, reading the key from
    the GEMINI_API_KEY env var. The Streamlit frontend just POSTs the idea and
    receives ready-to-save `code` + an `enhanced` design brief back.
    """
    try:
        enhanced, code = generate_game(req.prompt, style=req.style)
    except GameGenerationError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:  # noqa: BLE001 - surface unexpected failures cleanly
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}") from e
    return {"enhanced": enhanced, "code": code}


@app.get("/health")
def health():
    return {"status": "ok"}
