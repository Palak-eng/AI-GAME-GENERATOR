from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

import apiclient
from gen_features import get_api_base_message

st.set_page_config(
    page_title=" AI Game Maker",
    page_icon="🎮",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── Local library helpers (offline fallback) ────────────────────────────────
# Games can still be saved to a local folder so the app works even without the
# backend running. When the backend is reachable, the online gallery is used.


def _library_dir() -> Path:
    p = Path.home() / ".ai_game_lab"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _index_path() -> Path:
    return _library_dir() / "library.json"


def _load_library() -> list[dict]:
    import json

    idx = _index_path()
    if not idx.exists():
        return []
    try:
        return json.loads(idx.read_text(encoding="utf-8"))
    except Exception:
        return []


def _save_library(library: list[dict]):
    import json

    _index_path().write_text(json.dumps(library, ensure_ascii=False, indent=2), encoding="utf-8")


def _game_file(uid: str) -> Path:
    return _library_dir() / f"{uid}.html"


def _save_local(title: str, idea: str, style: str, enhanced: str, code: str) -> dict:
    import datetime
    import uuid

    uid = uuid.uuid4().hex[:12]
    record = {
        "id": uid,
        "title": title,
        "idea": idea,
        "style": style,
        "enhanced": enhanced,
        "created": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    _game_file(uid).write_text(code, encoding="utf-8")
    library = _load_library()
    library.insert(0, record)
    _save_library(library)
    return record


def _delete_local(uid: str):
    library = [g for g in _load_library() if g["id"] != uid]
    _save_library(library)
    f = _game_file(uid)
    if f.exists():
        f.unlink()


def _load_local(uid: str) -> str | None:
    f = _game_file(uid)
    return f.read_text(encoding="utf-8") if f.exists() else None


# ── App styling ──────────────────────────────────────────────────────────────
ui = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@500;700;800&family=Nunito:wght@500;700;900&display=swap');

    .stApp {
        background:
            radial-gradient(1200px 600px at 80% -10%, #2e1065 0%, transparent 60%),
            radial-gradient(1000px 500px at -10% 110%, #0f172a 0%, transparent 60%),
            #0b0f2a;
        color: #e2e8f0;
    }

    html, body, .stApp, .stMarkdown, p, label, input, textarea, button {
        font-family: 'Nunito', sans-serif !important;
    }

    .hero { text-align: center; padding: 2rem 0 0.5rem 0; }
    .hero h1 {
        font-family: 'Baloo 2', cursive !important;
        font-weight: 800;
        font-size: 3rem !important;
        background: linear-gradient(90deg, #f472b6, #a78bfa, #60a5fa, #34d399);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0 !important;
    }
    .hero .tagline {
        font-family: 'Nunito', sans-serif !important;
        color: #94a3b8;
        font-size: 1.1rem;
        margin-top: 0.25rem;
    }
    .hero .magic {
        display: inline-block;
        margin-top: 0.75rem;
        padding: 0.2rem 0.9rem;
        border-radius: 999px;
        background: rgba(139,92,246,0.15);
        border: 1px solid rgba(139,92,246,0.4);
        color: #c4b5fd;
        font-size: 0.8rem;
    }

    .stTextInput > label, .stSelectbox > label, .stRadio > label {
        color: #c4b5fd !important;
        font-weight: 800 !important;
        font-size: 0.95rem !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: rgba(30,27,75,0.6) !important;
        border: 1px solid #4338ca !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
        font-size: 1.05rem !important;
    }
    .stSelectbox [data-baseweb="select"] > div {
        background: rgba(30,27,75,0.6) !important;
        border: 1px solid #4338ca !important;
        border-radius: 12px !important;
        color: #f1f5f9 !important;
    }

    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #f472b6, #8b5cf6, #3b82f6) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.7rem 2rem !important;
        font-family: 'Baloo 2', cursive !important;
        font-weight: 800 !important;
        font-size: 1.1rem !important;
        box-shadow: 0 8px 30px rgba(139,92,246,0.45) !important;
        transition: transform 0.15s, box-shadow 0.15s;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 40px rgba(139,92,246,0.6) !important;
    }
    div[data-testid="stButton"] > button:not([kind="primary"]) {
        border-radius: 999px !important;
    }

    .enhanced-label {
        color: #f472b6; font-size: 0.75rem; font-weight: 900;
        letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 6px;
    }
    .enhanced-box {
        background: linear-gradient(135deg, #1e1b4b, #3b0764);
        border: 1px solid #7c3aed;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        color: #ddd6fe;
        font-size: 0.95rem;
        line-height: 1.6;
        margin: 0.25rem 0 1rem 0;
    }

    .stDownloadButton > button {
        background: linear-gradient(135deg, #059669, #0d9488) !important;
        color: #d1fae5 !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 800 !important;
    }
    .stAlert { border-radius: 12px !important; }
    .stCaption { color: #64748b !important; }
    .stExpander details { border-radius: 12px !important; }

    /* Gallery cards */
    .game-card {
        background: linear-gradient(135deg, #1e1b4b, #2e1065);
        border: 1px solid #4338ca;
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.6rem;
    }
    .game-card .g-title { color: #e2e8f0; font-weight: 800; font-size: 1.05rem; }
    .game-card .g-meta { color: #818cf8; font-size: 0.75rem; margin-top: 2px; }
    .game-card .g-idea { color: #94a3b8; font-size: 0.85rem; margin-top: 4px; }

    div[data-testid="stSidebar"] {
        background: #0e1330;
    }
</style>
"""
st.markdown(ui, unsafe_allow_html=True)

# ── API reachability check ──────────────────────────────────────────────────
# Free-tier Render services sleep after ~15 min idle and take 10-20s to wake,
# so a short timeout gives false "offline" errors. Use one longer timeout:
# it awaits the wake-up, yet still fails fast on a genuinely down host.
_online = False
_online_error = None
try:
    if apiclient.requests.get(f"{apiclient.BASE_URL}/health", timeout=30).status_code == 200:
        _online = True
except Exception as e:  # noqa: BLE001
    _online_error = str(e)


# ── Auth helpers ─────────────────────────────────────────────────────────────
def _logged_in() -> bool:
    return st.session_state.get("token") is not None


def show_login():
    st.markdown("## 👋 Welcome back!")
    mode = st.radio("Have an account?", ["Log in", "Create account"], horizontal=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Continue", type="primary"):
        if not username or not password:
            st.warning("Enter a username and password.")
            return
        try:
            if mode == "Create account":
                data = apiclient.register(username, password)
            else:
                data = apiclient.login(username, password)
        except apiclient.ApiError as e:
            st.error(f"😕 {e}")
            return
        st.session_state.token = data["token"]
        st.session_state.username = data["username"]
        st.rerun()


# ── Session state ────────────────────────────────────────────────────────────
if "prefill" not in st.session_state:
    st.session_state.prefill = ""
if "result" not in st.session_state:
    st.session_state.result = None
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "play_game_code" not in st.session_state:
    st.session_state.play_game_code = None
if "play_game_title" not in st.session_state:
    st.session_state.play_game_title = ""

# ── App body ─────────────────────────────────────────────────────────────────

# Hero (always shown)
st.markdown(
    """
    <div class='hero'>
        <h1>🎮 AI Game Maker</h1>
        <div class='tagline'>Type an idea → get a <b>finished playable game</b> in seconds.</div>
        <div class='magic'>✨ Powered by Gemini · Save &amp; play the shared gallery</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()

# Backend status banner
if not _online:
    st.info(
        f"⚠️ Game Lab backend is offline ({get_api_base_message(_online_error)}). "
        "You can still create games. Log in / save to the shared gallery needs the backend running."
    )

# Decide what to show: login gate OR main app
if _online and not _logged_in():
    show_login()
    st.stop()

# User header with logout
if _logged_in():
    cols = st.columns([3, 1, 1])
    with cols[0]:
        st.markdown(f"**👤 Logged in as {st.session_state.username}**")
    with cols[1]:
        if st.button("🪄 Make Game", use_container_width=True):
            st.session_state.view = "make"
    with cols[2]:
        if st.button("Log out", use_container_width=True):
            apiclient.logout(st.session_state.token)
            st.session_state.token = None
            st.session_state.username = None
            st.rerun()

    # Tabs
    tab_make, tab_gallery, tab_mine = st.tabs(["🪄 Make a Game", "🌍 Gallery", "📦 My Games"])
else:
    tab_make, tab_gallery = st.tabs(["🪄 Make a Game", "🌍 Gallery"])
    tab_mine = None

# ── Tab: Make a Game ─────────────────────────────────────────────────────────
with tab_make:
    EXAMPLES = [
        ("🚀", "space shooter"),
        ("🐍", "snake game"),
        ("🏓", "pong"),
        ("🧱", "breakout"),
        ("🐱", "cat jumps over dogs"),
        ("🍎", "catch falling fruits"),
        ("🧟", "zombie survival"),
        ("🐠", "fish dodges sharks"),
    ]

    st.markdown("<b>✨ Tap an idea to start:</b>", unsafe_allow_html=True)
    chips = st.columns(len(EXAMPLES))
    for col, (emoji, label) in zip(chips, EXAMPLES, strict=True):
        with col:
            if st.button(f"{emoji} {label}", key=f"chip_{label}", use_container_width=True):
                st.session_state.prefill = label
    st.markdown("")

    col1, col2 = st.columns([3, 1])
    with col1:
        user_prompt = st.text_input(
            "Your game idea",
            value=st.session_state.prefill,
            placeholder="e.g. a tiny robot collecting stars in space",
        )
    with col2:
        style = st.selectbox("Art style", ["arcade", "retro", "space", "fantasy", "minimal"])

    if st.button("⚡ Make My Game!", type="primary", use_container_width=True):
        prompt = user_prompt.strip()
        if not prompt:
            st.warning("Type a game idea first — even just 2 words like 'ninja jump' works!")
        else:
            st.session_state.play_game_code = None
            if _online:
                pipeline = st.status(
                    "🧠 Starting your game idea... (this runs on the server, takes 20–40s)",
                    expanded=True,
                )
                try:
                    result = apiclient.generate(prompt, style=style, timeout=150)
                    st.session_state.result = {
                        "enhanced": result.get("enhanced", prompt),
                        "code": result["code"],
                        "idea": prompt,
                    }
                    pipeline.update(label="🎉 Game ready!", state="complete", expanded=False)
                except apiclient.ApiError as e:
                    st.session_state.result = None
                    pipeline.update(label="😕 Generation failed", state="error", expanded=False)
                    st.error(f"😕 {e}")
                except Exception:
                    st.session_state.result = None
                    pipeline.update(label="😕 Generation failed", state="error", expanded=False)
                    st.error(
                        "😕 Something unexpected went wrong while generating your game. "
                        "Please try again in a moment."
                    )
            else:
                st.warning(
                    "⚠️ The AI service isn't reachable right now, so I can't generate new games. "
                    "Please check the connection and try again."
                )

    # Render freshly generated game
    if st.session_state.result:
        result = st.session_state.result
        st.markdown("### 🎉 Your new game is ready!")
        components.html(result["code"], height=660, scrolling=False)
        st.markdown(
            f"<div class='enhanced-label'>✨ AI upgraded your idea to:</div>"
            f"<div class='enhanced-box'>{result['enhanced']}</div>",
            unsafe_allow_html=True,
        )

        st.markdown("### 💾 Save your game")
        c1, c2 = st.columns([3, 1])
        with c1:
            save_title = st.text_input(
                "Title", placeholder="e.g. Star Robot Adventure", key="save_title"
            )
        with c2:
            st.markdown("")
            st.markdown("")
            is_public = st.checkbox("Share in gallery", value=True)
        if st.button("💾 Save", type="primary"):
            title = (save_title.strip() or result["idea"] or "My Game").title()
            if _online and _logged_in():
                try:
                    apiclient.create_game(
                        st.session_state.token,
                        title,
                        result["idea"],
                        style,
                        result["code"],
                        1 if is_public else 0,
                    )
                    st.success(f"Saved “{title}” to your account!")
                except apiclient.ApiError as e:
                    st.error(f"Couldn't save online: {e}")
            else:
                _save_local(title, result["idea"], style, result["enhanced"], result["code"])
                st.success(f"Saved “{title}” to your local library!")

        st.markdown("### 📤 Download & share")
        st.download_button(
            "⬇️ Download game.html",
            data=result["code"],
            file_name="game.html",
            mime="text/html",
            use_container_width=True,
        )
        st.caption(
            "The download is a single `game.html` file — double-click anytime to play, "
            "or send to a friend on WhatsApp/Drive; it works on any device."
        )
        with st.expander("👨‍💻 View the generated code"):
            st.code(result["code"], language="html")

# ── Tab: Gallery ─────────────────────────────────────────────────────────────
with tab_gallery:
    st.markdown("## 🌍 Community Gallery")
    st.caption("Games everyone has shared. Click Play to try one!")
    if _online and _logged_in():
        try:
            gallery = apiclient.list_gallery(st.session_state.token)
            if not gallery:
                st.write("No games shared yet. Be the first!")
            for g in gallery:
                with st.container():
                    st.markdown(
                        f"<div class='game-card'>"
                        f"<div class='g-title'>🎮 {g['title']}</div>"
                        f"<div class='g-meta'>by {g['owner']} · {g['style']} · {g['idea']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    if st.button("▶ Play", key=f"gal_play_{g['id']}", use_container_width=True):
                        try:
                            full = apiclient.get_game(st.session_state.token, g["id"])
                            st.session_state.play_game_code = full["code"]
                            st.session_state.play_game_title = g["title"]
                            st.rerun()
                        except apiclient.ApiError as e:
                            st.error(f"Couldn't load game: {e}")
        except apiclient.ApiError as e:
            st.error(f"Couldn't load gallery: {e}")
    else:
        st.write("Log in to browse and share the community gallery.")

# ── Tab: My Games ────────────────────────────────────────────────────────────
if tab_mine is not None:
    with tab_mine:
        st.markdown("## 📦 My Games")
        try:
            mine = apiclient.list_mine(st.session_state.token)
            if not mine:
                st.write("You haven't saved any games yet.")
            for g in mine:
                with st.container():
                    visibility = "🌍 public" if g["is_public"] else "🔒 private"
                    st.markdown(
                        f"<div class='game-card'>"
                        f"<div class='g-title'>🎮 {g['title']} "
                        f"<span style='color:#64748b'>· {visibility}</span></div>"
                        f"<div class='g-meta'>{g['style']} · {g['idea']}</div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                    c1, c2, c3, c4 = st.columns(4)
                    with c1:
                        if st.button("▶ Play", key=f"my_play_{g['id']}", use_container_width=True):
                            full = apiclient.get_game(st.session_state.token, g["id"])
                            st.session_state.play_game_code = full["code"]
                            st.session_state.play_game_title = g["title"]
                            st.rerun()
                    with c2:
                        new_vis = 0 if g["is_public"] else 1
                        btn = "🔒 Make private" if g["is_public"] else "🌍 Make public"
                        if st.button(btn, key=f"my_vis_{g['id']}", use_container_width=True):
                            apiclient.update_game(
                                st.session_state.token, g["id"], is_public=new_vis
                            )
                            st.rerun()
                    with c3:
                        if st.button("⬇️ Code", key=f"my_dl_{g['id']}", use_container_width=True):
                            full = apiclient.get_game(st.session_state.token, g["id"])
                            st.session_state.pending_download = full
                            st.rerun()
                    with c4:
                        if st.button("🗑", key=f"my_del_{g['id']}", use_container_width=True):
                            apiclient.delete_game(st.session_state.token, g["id"])
                            st.rerun()
        except apiclient.ApiError as e:
            st.error(f"Couldn't load your games: {e}")

# Handle a pending download (show download button after rerun)
pending = st.session_state.get("pending_download")
if pending:
    st.download_button(
        "⬇️ Download this game",
        data=pending["code"],
        file_name="game.html",
        mime="text/html",
    )
    st.session_state.pending_download = None

# ── Play the selected game (from gallery or my games) ───────────────────────
if st.session_state.play_game_code:
    st.markdown("---")
    st.markdown(f"### 🕹️ Playing: {st.session_state.play_game_title}")
    components.html(st.session_state.play_game_code, height=660, scrolling=False)
    if st.button("Close game", use_container_width=True):
        st.session_state.play_game_code = None
        st.rerun()
