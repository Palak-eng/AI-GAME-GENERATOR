import os
import tempfile
import uuid

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.mktemp(suffix='.db')}"

from fastapi.testclient import TestClient

from api import app

client = TestClient(app)


def _register(username=None, password="secret123"):
    if username is None:
        username = f"user_{uuid.uuid4().hex[:8]}"
    return client.post("/api/register", json={"username": username, "password": password})


def _headers(token):
    return {"Authorization": f"Bearer {token}"}


class TestAuth:
    def test_register_returns_token(self):
        r = _register("alice", "passw0rd")
        assert r.status_code == 201
        data = r.json()
        assert data["username"] == "alice"
        assert data["token"]

    def test_duplicate_username_rejected(self):
        _register("dupe", "passw0rd")
        r = _register("dupe", "something")
        assert r.status_code == 409

    def test_login_success(self):
        _register("carol", "passw0rd")
        r = client.post("/api/login", json={"username": "carol", "password": "passw0rd"})
        assert r.status_code == 200
        assert r.json()["token"]

    def test_login_wrong_password(self):
        _register("dave", "passw0rd")
        r = client.post("/api/login", json={"username": "dave", "password": "wrong"})
        assert r.status_code == 401

    def test_me_requires_auth(self):
        r = client.get("/api/me")
        assert r.status_code == 401

    def test_me_with_token(self):
        t = _register("erin").json()["token"]
        r = client.get("/api/me", headers=_headers(t))
        assert r.status_code == 200
        assert r.json()["username"] == "erin"


class TestGames:
    def _setup(self):
        t = _register().json()["token"]
        return t, _headers(t)

    def test_create_game(self):
        token, headers = self._setup()
        code = "<!DOCTYPE html><html><body><canvas></canvas><script>loop();</script></body></html>"
        r = client.post(
            "/api/games",
            json={"title": "Star Run", "idea": "run through space", "style": "space", "code": code},
            headers=headers,
        )
        assert r.status_code == 201
        assert r.json()["title"] == "Star Run"

    def test_list_requires_auth(self):
        r = client.get("/api/games")
        assert r.status_code == 401

    def test_gallery_lists_public_games_only(self):
        token, headers = self._setup()
        client.post(
            "/api/games",
            json={"title": "Public", "code": "<html></html>" * 3, "idea": "x", "is_public": 1},
            headers=headers,
        )
        client.post(
            "/api/games",
            json={"title": "Private", "code": "<html></html>" * 3, "idea": "x", "is_public": 0},
            headers=headers,
        )
        # Anyone logged in can see the shared gallery
        t2 = _register("gina").json()["token"]
        r = client.get("/api/games", headers=_headers(t2))
        titles = [g["title"] for g in r.json()]
        assert "Public" in titles
        assert "Private" not in titles

    def test_mine_returns_only_my_games(self):
        token, headers = self._setup()
        client.post(
            "/api/games",
            json={"title": "Mine1", "code": "<html></html>" * 3, "idea": "x"},
            headers=headers,
        )
        t2 = _register("heidi").json()["token"]
        h2 = _headers(t2)
        client.post(
            "/api/games",
            json={"title": "Mine2", "code": "<html></html>" * 3, "idea": "x"},
            headers=h2,
        )
        mine = client.get("/api/games?mine=true", headers=headers).json()
        assert [g["title"] for g in mine] == ["Mine1"]

    def test_cannot_get_private_game(self):
        token, headers = self._setup()
        created = client.post(
            "/api/games",
            json={"title": "Secret", "code": "<html></html>" * 3, "idea": "x", "is_public": 0},
            headers=headers,
        ).json()
        t2 = _register("ivan").json()["token"]
        r = client.get(f"/api/games/{created['id']}", headers=_headers(t2))
        assert r.status_code == 403

    def test_delete_own_game(self):
        token, headers = self._setup()
        created = client.post(
            "/api/games",
            json={"title": "Temp", "code": "<html></html>" * 3, "idea": "x"},
            headers=headers,
        ).json()
        r = client.delete(f"/api/games/{created['id']}", headers=headers)
        assert r.status_code == 204

    def test_cannot_delete_others_game(self):
        token, headers = self._setup()
        created = client.post(
            "/api/games",
            json={"title": "NotYours", "code": "<html></html>" * 3, "idea": "x"},
            headers=headers,
        ).json()
        t2 = _register("judy").json()["token"]
        r = client.delete(f"/api/games/{created['id']}", headers=_headers(t2))
        assert r.status_code == 404


class TestHealth:
    def test_health(self):
        assert client.get("/health").json() == {"status": "ok"}


class TestGenerate:
    def test_generate_returns_code(self, monkeypatch):
        def fake_generate(prompt, style="arcade"):
            return "✨ Enhanced idea", "<!DOCTYPE html><html><body><canvas></canvas></body></html>"

        monkeypatch.setattr("api.generate_game", fake_generate)
        r = client.post("/api/generate", json={"prompt": "cat jumps over dogs", "style": "retro"})
        assert r.status_code == 200
        body = r.json()
        assert body["enhanced"] == "✨ Enhanced idea"
        assert "<html>" in body["code"]

    def test_generate_requires_prompt(self):
        r = client.post("/api/generate", json={"style": "arcade"})
        assert r.status_code == 422

    def test_generate_surfaces_generation_error(self, monkeypatch):
        from generator import GameGenerationError

        def fake_bad(prompt, style="arcade"):
            raise GameGenerationError("oops, no key")

        monkeypatch.setattr("api.generate_game", fake_bad)
        r = client.post("/api/generate", json={"prompt": "x", "style": "arcade"})
        assert r.status_code == 502
        assert "oops, no key" in r.json()["detail"]
