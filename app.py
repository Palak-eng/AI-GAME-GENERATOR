import streamlit as st
import os
import uuid
from generator import generate_game, GameGenerationError

st.set_page_config(page_title="🎮 AI Game Generator", page_icon="🎮", layout="centered")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@700&family=Inter:wght@400;600&display=swap');

    .stApp { background: #0a0a1a; }

    h1 {
        font-family: 'Orbitron', monospace !important;
        background: linear-gradient(135deg, #a78bfa, #60a5fa, #f472b6);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem !important;
    }

    .subtitle { color: #64748b; font-family: Inter, sans-serif; margin-top: -10px; }

    .stTextInput > label, .stSelectbox > label {
        color: #c4b5fd !important;
        font-weight: 600;
        font-family: Inter, sans-serif;
    }

    /* Main generate button */
    div[data-testid="stButton"]:first-of-type > button {
        background: linear-gradient(135deg, #7c3aed, #4f46e5, #2563eb);
        color: white; border: none; border-radius: 12px;
        padding: 0.75rem 2rem; font-size: 1.1rem; font-weight: 700;
        width: 100%; letter-spacing: 0.5px;
        box-shadow: 0 4px 24px rgba(124,58,237,0.4);
        transition: all 0.2s;
    }
    div[data-testid="stButton"]:first-of-type > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 32px rgba(124,58,237,0.6);
    }

    .enhanced-box {
        background: linear-gradient(135deg, #1e1b4b, #1e3a5f);
        border: 1px solid #4f46e5;
        border-radius: 12px;
        padding: 1rem 1.2rem;
        color: #c7d2fe;
        font-size: 0.9rem;
        line-height: 1.6;
        margin: 0.5rem 0 1rem 0;
    }
    .enhanced-label {
        color: #818cf8; font-size: 0.75rem; font-weight: 700;
        letter-spacing: 1px; text-transform: uppercase; margin-bottom: 6px;
    }

    .example-btn button {
        background: #1e1b4b !important;
        color: #a5b4fc !important;
        border: 1px solid #4338ca !important;
        border-radius: 8px !important;
        font-size: 0.78rem !important;
        padding: 0.3rem 0.5rem !important;
    }
    .example-btn button:hover {
        background: #312e81 !important;
        border-color: #818cf8 !important;
    }

    .stAlert { border-radius: 10px; }
    .stDownloadButton > button {
        background: #064e3b !important;
        color: #6ee7b7 !important;
        border: 1px solid #059669 !important;
        border-radius: 8px !important;
        width: 100%;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ───────────────────────────────────────────────────────────────────
st.markdown("<h1>🎮 AI Game Generator</h1>", unsafe_allow_html=True)
st.markdown("<p class='subtitle'>Just type a simple idea — AI will design and build the whole game for you!</p>",
            unsafe_allow_html=True)
st.divider()

# ── Example prompts ──────────────────────────────────────────────────────────
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

st.markdown("<p style='color:#475569;font-size:0.8rem;margin-bottom:4px;'>✨ Quick ideas — click any:</p>",
            unsafe_allow_html=True)

# ── Session state setup ──────────────────────────────────────────────────────
# A unique per-browser-session ID, used to keep each user's generated file separate
if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex[:8]

if "prefill" not in st.session_state:
    st.session_state.prefill = ""

# Holds the most recent successful generation so it survives reruns
# (e.g. clicking an example chip, or any other widget interaction)
if "result" not in st.session_state:
    st.session_state.result = None  # will hold {"enhanced": str, "code": str, "path": str}

cols = st.columns(len(EXAMPLES))
for col, (emoji, label) in zip(cols, EXAMPLES):
    with col:
        st.markdown('<div class="example-btn">', unsafe_allow_html=True)
        if st.button(f"{emoji} {label}", key=f"ex_{label}", use_container_width=True):
            st.session_state.prefill = label
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Input row ────────────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    user_prompt = st.text_input(
        "Your game idea",
        value=st.session_state.prefill,
        placeholder="e.g. dinosaur runs and jumps over rocks",
    )
with col2:
    style = st.selectbox("Style", ["arcade", "space", "retro", "fantasy", "minimal"])

st.markdown("<br>", unsafe_allow_html=True)

# ── Generate button ──────────────────────────────────────────────────────────
if st.button("⚡ Generate My Game!", use_container_width=True):
    prompt = user_prompt.strip()
    if not prompt:
        st.warning("Type a game idea first — even just 2 words like 'ninja jump' works!")
    else:
        with st.spinner("🧠 AI is designing, coding, and polishing your game... this can take up to a minute"):
            try:
                enhanced, code = generate_game(prompt, style=style)

                # Save file in a per-session folder so concurrent users don't collide
                out_dir = os.path.join("generated_games", st.session_state.session_id)
                os.makedirs(out_dir, exist_ok=True)
                out_path = os.path.join(out_dir, "game.py")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(code)

                # Persist results in session_state so they survive reruns
                st.session_state.result = {
                    "enhanced": enhanced,
                    "code": code,
                    "path": out_path,
                }

            except GameGenerationError as e:
                st.session_state.result = None
                st.error(f"😕 {e}")
            except Exception:
                st.session_state.result = None
                st.error(
                    "😕 Something unexpected went wrong while generating your game. "
                    "Please try again in a moment."
                )

# ── Display results (persists across reruns via session_state) ──────────────
if st.session_state.result:
    result = st.session_state.result

    st.markdown(
        f"<div class='enhanced-label'>✨ AI upgraded your idea to:</div>"
        f"<div class='enhanced-box'>{result['enhanced']}</div>",
        unsafe_allow_html=True
    )

    st.success(f"🎉 Game ready! Run it locally with: `python {result['path']}`")

    st.download_button(
        "⬇️ Download game.py",
        data=result["code"],
        file_name="game.py",
        mime="text/plain",
        use_container_width=True,
        key="download_game_btn",
    )

    with st.expander("👨‍💻 View the generated code"):
        st.code(result["code"], language="python")