"""
Small HTTP client for talking to the Game Maker API from the Streamlit UI.

Base URL comes from the API_BASE_URL env var (e.g. https://my-api.onrender.com).
If unset, defaults to http://localhost:8000 (the local uvicorn server).
"""

import os

import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


class ApiError(Exception):
    pass


def register(username: str, password: str) -> dict:
    payload = {"username": username, "password": password}
    r = requests.post(f"{BASE_URL}/api/register", json=payload, timeout=35)
    return _handle(r)


def login(username: str, password: str) -> dict:
    payload = {"username": username, "password": password}
    r = requests.post(f"{BASE_URL}/api/login", json=payload, timeout=35)
    return _handle(r)


def logout(token: str):
    _handle(requests.post(f"{BASE_URL}/api/logout", headers=_auth(token), timeout=35))


def me(token: str) -> dict:
    return _handle(requests.get(f"{BASE_URL}/api/me", headers=_auth(token), timeout=35))


def create_game(
    token: str, title: str, idea: str, style: str, code: str, is_public: int = 1
) -> dict:
    payload = {
        "title": title,
        "idea": idea,
        "style": style,
        "code": code,
        "is_public": is_public,
    }
    r = requests.post(f"{BASE_URL}/api/games", json=payload, headers=_auth(token), timeout=35)
    return _handle(r)


def list_gallery(token: str) -> list:
    r = requests.get(f"{BASE_URL}/api/games", headers=_auth(token), timeout=35)
    return _handle(r)


def list_mine(token: str) -> list:
    r = requests.get(f"{BASE_URL}/api/games?mine=true", headers=_auth(token), timeout=35)
    return _handle(r)


def generate(prompt: str, style: str = "arcade", timeout: int = 120) -> dict:
    """Ask the backend to generate a game (runs Gemini server-side)."""
    payload = {"prompt": prompt, "style": style}
    r = requests.post(f"{BASE_URL}/api/generate", json=payload, timeout=timeout)
    return _handle(r)


def get_game(token: str, game_id: int) -> dict:
    r = requests.get(f"{BASE_URL}/api/games/{game_id}", headers=_auth(token), timeout=35)
    return _handle(r)


def update_game(
    token: str,
    game_id: int,
    is_public: int | None = None,
    title: str | None = None,
) -> dict:
    payload = {}
    if is_public is not None:
        payload["is_public"] = is_public
    if title is not None:
        payload["title"] = title
    url = f"{BASE_URL}/api/games/{game_id}"
    r = requests.patch(url, json=payload, headers=_auth(token), timeout=35)
    return _handle(r)


def delete_game(token: str, game_id: int):
    r = requests.delete(f"{BASE_URL}/api/games/{game_id}", headers=_auth(token), timeout=35)
    if r.status_code == 204:
        return {"ok": True}
    return _handle(r)


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _handle(r: requests.Response):
    try:
        body = r.json()
    except Exception:
        body = r.text
    if r.status_code >= 400:
        detail = body.get("detail", body) if isinstance(body, dict) else body
        raise ApiError(str(detail))
    return body
