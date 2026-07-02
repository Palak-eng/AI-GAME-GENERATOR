from google import genai
from dotenv import load_dotenv
import os
import re
import subprocess
import tempfile
import shutil

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is not set. Add it to your .env file as "
        "GEMINI_API_KEY=your_key_here before running the app."
    )

client = genai.Client(api_key=API_KEY)


# ─── Custom exception for clean error surfacing in the UI ───────────────────

class GameGenerationError(Exception):
    """Raised when prompt enhancement or code generation fails in a known way."""
    pass


# ─── Prompt Enhancer ─────────────────────────────────────────────────────────

ENHANCER_PROMPT = """You are a game design expert helping kids create amazing games.

A kid typed a simple game idea. Your job is to expand it into a RICH, DETAILED game design prompt.

Rules:
- Keep the core idea the same
- Add: specific visual details, character descriptions, enemy types, power-ups, background details, color themes, sound mood
- Add: clear win/lose condition, scoring system, difficulty progression
- Make it exciting and fun-sounding
- Keep all content suitable for children (no graphic violence or gore, even for "survival" or "zombie" themes — keep it cartoonish and silly)
- Output ONLY the improved prompt, nothing else. No intro, no explanation.

Kid's idea: {user_prompt}

Improved game design prompt:"""


def _extract_text(response) -> str:
    """
    Safely extract text from a Gemini response.
    Raises GameGenerationError with a clear message if the response is empty/blocked.
    """
    text = getattr(response, "text", None)
    if text is None or not text.strip():
        reason = None
        try:
            candidates = getattr(response, "candidates", None)
            if candidates:
                reason = getattr(candidates[0], "finish_reason", None)
        except Exception:
            pass
        if reason:
            raise GameGenerationError(
                f"The AI couldn't generate a response (reason: {reason}). "
                "Try rephrasing your game idea."
            )
        raise GameGenerationError(
            "The AI returned an empty response. Please try again or rephrase your idea."
        )
    return text.strip()


def _call_model(contents: str, temperature: float, max_output_tokens: int):
    """Wraps the Gemini API call with consistent error handling."""
    try:
        response = client.models.generate_content(
            model="models/gemini-2.5-flash",
            contents=contents,
            config={"temperature": temperature, "max_output_tokens": max_output_tokens},
        )
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str or "quota" in err_str.lower():
            raise GameGenerationError(
                "🚦 The Gemini API's free-tier quota is used up for now (free keys are capped "
                "at a small number of requests per day/minute, and each game generation uses "
                "several requests). Wait a bit and try again, or switch to a Gemini API key with "
                "billing enabled for higher limits — see "
                "https://ai.google.dev/gemini-api/docs/rate-limits"
            ) from e
        raise GameGenerationError(f"Couldn't reach the AI service: {e}") from e
    return _extract_text(response)


def enhance_prompt(user_prompt: str) -> str:
    """Turn a simple kid's idea into a rich game design prompt."""
    return _call_model(
        ENHANCER_PROMPT.format(user_prompt=user_prompt),
        temperature=0.9,
        max_output_tokens=512,
    )


# ─── Game Generator (HTML5 Canvas — runs instantly in any browser) ──────────
# We generate a SINGLE self-contained .html file (inline <style> + <script>,
# no external assets) so it:
#   1) plays instantly inside the app (embedded in an iframe)
#   2) can be downloaded as one file and re-opened / replayed anytime
#   3) can be shared with a friend (WhatsApp/email/Drive) — they just
#      double-click it and it opens in their browser, no installs needed.
#
# NOTE: prompt-enhancement and code generation are combined into ONE API call
# (see generate_game below) instead of two separate calls. Free-tier Gemini
# keys have tight daily/per-minute quotas, and every request counts — this
# cuts the baseline requests-per-generation roughly in half.

GAME_DESIGN_RULES = """You are also a game design expert helping kids create amazing games.
Before writing code, mentally expand the kid's simple idea into a RICH, DETAILED game design:
- Keep the core idea the same
- Add: specific visual details, character descriptions, enemy types, power-ups, background details, color themes, sound mood
- Add: clear win/lose condition, scoring system, difficulty progression
- Make it exciting and fun-sounding
- Keep all content suitable for children (no graphic violence or gore, even for "survival" or "zombie" themes — keep it cartoonish and silly)
"""

SYSTEM_PROMPT = """You are a senior HTML5 game developer who makes VISUALLY STUNNING browser games
using the Canvas 2D API and vanilla JavaScript. These games are for kids — they must look
colorful, exciting, and polished, and must run by simply opening an HTML file in a browser.

════════════════════════════════════════════════
 OUTPUT FORMAT — CRITICAL
════════════════════════════════════════════════
- Output ONE complete, self-contained HTML document. Nothing else.
- Structure: <!DOCTYPE html><html>...<head><style>...</style></head><body>
  <canvas id="game" width="800" height="600"></canvas><script>...</script></body></html>
- Everything (CSS + JS) must be INLINE in that one file. No external libraries, no CDN links,
  no external images/fonts/audio files (use Web Audio API oscillators if you want sound, optional).
- Zero markdown. Zero backticks. Zero explanations before or after the HTML.
- The very last line of your output must be </html>.
- CRITICAL: Code must be 100% complete and runnable. Never stop halfway.

════════════════════════════════════════════════
 GRAPHICS — THIS IS THE MOST IMPORTANT SECTION
════════════════════════════════════════════════

RULE 1 — NO PLAIN RECTANGLES FOR CHARACTERS:
Every character, enemy, player, boss, power-up MUST be drawn with at least 3-4 canvas draw calls combined
(arc, moveTo/lineTo paths, bezierCurveTo, etc.) — never a single fillRect.
Examples:
  - Spaceship: polygon body (ctx.beginPath + lineTo triangle) + 2 small wing triangles + circle cockpit (arc) + engine glow (radial gradient circle)
  - Character: circle head (arc) + rounded body (ellipse or rounded rect) + line arms + line legs
  - Animal: large circle body + small circle head + triangle ears + dot eyes

RULE 2 — RICH BACKGROUNDS (never solid black or white):
Choose ONE of these and implement it fully:
  Option A — Gradient sky: ctx.createLinearGradient across the canvas height
  Option B — Starfield: 150 randomly placed white/yellow dots of varying sizes (1-3px), redrawn each frame
  Option C — Tiled pattern: repeating shapes (clouds, bricks, grass tiles, hex grid) across the canvas
  Option D — Layered parallax: 2-3 layers of simple shapes scrolling at different speeds

RULE 3 — PARTICLES & EFFECTS:
Include at least 2 of these:
  - Explosion particles: on enemy death, spawn 8-12 small circles flying outward, fading over ~0.5s (track particle objects in an array, update + draw each frame)
  - Glow effect: draw the same shape 2-3x with decreasing size/increasing alpha (radial gradient or shadowBlur)
  - Screen flash: on player hit, briefly fill canvas with a semi-transparent red rectangle
  - Trail effect: store the last 5 positions of the player/bullet, draw fading circles along the path
  - Score popup: floating "+100" text that rises and fades when scoring

RULE 4 — COLOR PALETTE:
Define at least 8 named color constants (JS consts, hex strings) at the top of the script.
Use jewel tones, neons, or pastels — never just red/green/blue.
Example palettes:
  Neon: #FF00FF, #00FFFF, #FF6600, #00FF66, #FFD700, #FF0055, #0066FF, #CCFF00
  Jewel: #8B00FF, #FF1493, #00CED1, #FFD700, #FF4500, #32CD32, #1E90FF, #FF69B4
  Pastel: #FFB3BA, #FFDFBA, #FFFFBA, #BAFFC9, #BAE1FF, #E8BAFF, #FFBAF3, #BAFFF0

RULE 5 — UI POLISH:
  - Score/lives text: draw shadow first (dark color, +2px offset), then bright text on top
  - Health bar: rounded rect background (dark) + colored fill + white border
  - Game Over screen: semi-transparent dark overlay + big styled text + "Press R or tap to restart" hint

════════════════════════════════
 GAMEPLAY REQUIREMENTS
════════════════════════════════
- Fun and immediately playable by a child, mouse/touch AND keyboard both work
- Scoring system shown on screen at all times
- Clear win condition OR survive-as-long-as-possible with high score
- At least 2 different enemy/obstacle types with different behaviors
- At least 1 power-up or bonus item
- Controls: Arrow keys or WASD for movement, SPACE to shoot/jump. ALSO support click/tap
  (so it works on phones/tablets when a friend opens the shared file)
- Difficulty increases over time (enemies get faster, more spawn, etc.)
- On Game Over: show "Press R or tap Restart button to play again" — clicking/tapping restarts
  the game WITHOUT needing to reload the page (reset all game state variables and resume the loop)
- REPLAYABILITY IS CRITICAL: the restart must fully reset score, entities, and difficulty so the
  SAME file can be played again and again with no reload
- Keep all themes child-friendly and cartoonish, even for "survival" or "battle" ideas — no
  realistic violence or gore

════════════════════════════════
 CODE REQUIREMENTS
════════════════════════════════
- Use requestAnimationFrame for the game loop (not setInterval)
- canvas width=800 height=600, set via the <canvas> tag attributes
- Add a viewport meta tag and a little CSS so the canvas is centered with a dark page background
  (so it looks good full-screen when opened directly)
- document.title should be a short fun name for the game
- No empty function bodies, no placeholder comments — every function fully implemented
- Wrap the game in an IIFE or DOMContentLoaded listener so it runs immediately on file open

ABSOLUTELY FORBIDDEN:
- Single-color rectangles for any game character or enemy
- Solid black/white background with no detail
- Any external script/link/image/font references (must be 100% self-contained, works offline)
- Any non-HTML/CSS/JS text in output
- Incomplete code that cuts off before </html>
"""

MAX_CONTINUATIONS = 2


def clean_code(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def _node_syntax_check(js_code: str):
    """
    Runs `node --check` on extracted JS to catch real syntax errors (unclosed
    braces/brackets/strings, cut-off statements, etc).
    Returns True (valid), False (invalid), or None if Node isn't available or
    the check itself couldn't run — in which case we don't penalize the code.
    """
    node_path = shutil.which("node")
    if not node_path:
        return None
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", suffix=".js", delete=False, encoding="utf-8"
        ) as f:
            f.write(js_code)
            tmp_path = f.name
        result = subprocess.run(
            [node_path, "--check", tmp_path],
            capture_output=True,
            text=True,
            timeout=10,
        )
        return result.returncode == 0
    except Exception:
        return None
    finally:
        if tmp_path:
            try:
                os.remove(tmp_path)
            except OSError:
                pass


def is_code_complete(code: str) -> bool:
    """
    Completeness check for a self-contained HTML5 canvas game.
    Checks structural markers a finished file must have, then — if Node is
    available — runs a real JS syntax check on the extracted <script> content
    instead of a naive brace count (which false-positives constantly on real
    JS: comments, strings, and template literals routinely contain unmatched
    braces even in perfectly valid, complete code).
    """
    lower = code.lower()

    has_doctype_ish = "<html" in lower
    ends_properly = lower.rstrip().endswith("</html>")
    has_canvas = "<canvas" in lower
    has_loop = "requestanimationframe" in lower
    has_script_close = "</script>" in lower

    if not (has_doctype_ish and ends_properly and has_canvas and has_loop and has_script_close):
        return False

    match = re.search(r"<script[^>]*>(.*)</script>", code, re.DOTALL | re.IGNORECASE)
    if match:
        js_result = _node_syntax_check(match.group(1))
        if js_result is False:
            return False
        # js_result is True, or None (Node unavailable) — either way, don't block on it

    return True


def continue_code(partial_code: str, enhanced_prompt: str, style_desc: str) -> str:
    continuation_prompt = f"""You were writing a self-contained HTML5 Canvas game for: "{enhanced_prompt}" (style: {style_desc})

The HTML/JS below is INCOMPLETE — it got cut off mid-way:

{partial_code}

Continue EXACTLY from where it stopped. Output ONLY the remaining HTML/JS/CSS.
Do NOT repeat anything already written. Start from the cut-off point.
The final lines must properly close the game loop, </script>, </body>, and </html>.
Output ONLY code. No markdown. No explanations."""

    text = _call_model(continuation_prompt, temperature=0.3, max_output_tokens=8192)
    return clean_code(text)


def _parse_combined_response(raw_text: str, fallback_prompt: str) -> tuple[str, str]:
    """
    Parses a single model response that should contain both the enhanced
    design brief and the full game code, separated by marker lines.
    Falls back gracefully if the model didn't follow the marker format
    exactly (e.g. found the HTML start directly, or worst case treats the
    whole response as code).
    """
    text = raw_text.strip()

    match = re.search(
        r"===\s*ENHANCED PROMPT\s*===(.*?)===\s*GAME CODE\s*===(.*)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if match:
        enhanced = match.group(1).strip()
        code = clean_code(match.group(2))
        if enhanced and code:
            return enhanced, code

    # Fallback: markers missing/malformed — locate where the HTML actually starts
    html_start = re.search(r"<!DOCTYPE html", text, re.IGNORECASE)
    if html_start:
        enhanced = text[: html_start.start()].strip()
        enhanced = re.sub(r"===.*?===", "", enhanced, flags=re.DOTALL).strip()
        code = clean_code(text[html_start.start():])
        return (enhanced or f"A fun {fallback_prompt} game, brought to life!"), code

    # Last resort: treat everything as code
    return f"A fun {fallback_prompt} game, brought to life!", clean_code(text)


def generate_game(prompt: str, style: str = "arcade", on_progress=None) -> tuple[str, str]:
    """
    Returns (enhanced_prompt, game_html) so the UI can show what was improved
    and embed/play the game directly in the browser.
    Raises GameGenerationError on any failure, with a user-safe message.

    on_progress, if given, is called as on_progress(percent: int, message: str)
    at each stage of the pipeline so the caller (e.g. a Streamlit UI) can
    render live progress instead of a plain spinner.

    Prompt-enhancement and code generation happen in a SINGLE API call (not
    two) to conserve quota on free-tier Gemini keys — see the note above
    SYSTEM_PROMPT.
    """
    def report(pct: int, msg: str):
        if on_progress:
            on_progress(pct, msg)

    style_hints = {
        "arcade": "Classic arcade — vibrant neon colors, dark background, fast action.",
        "retro": "16-bit retro — punchy limited palette, pixel-art inspired shapes.",
        "space": "Space adventure — starfield background, glowing ships, laser beams.",
        "fantasy": "Fantasy RPG — jewel tone palette, magical glowing particles, rich scenery.",
        "minimal": "Clean minimal — white/pastel background, bold geometric shapes, smooth animation.",
    }
    style_desc = style_hints.get(style, style_hints["arcade"])

    report(5, "🧠 Reading your idea...")

    full_prompt = f"""{GAME_DESIGN_RULES}

{SYSTEM_PROMPT}

Visual style: {style_desc}
Kid's idea: {prompt}

Do BOTH of these in this single response, outputting EXACTLY in this format and nothing else
(no extra commentary before, between, or after):

===ENHANCED PROMPT===
(the improved, rich game design brief — 3-6 exciting sentences, plain text only)
===GAME CODE===
(the COMPLETE self-contained HTML file — must start with <!DOCTYPE html> and end with </html>)

Begin now:"""

    report(25, "🎨 Designing & writing your full game in one go... (the big step, can take 20-40s)")
    raw_text = _call_model(full_prompt, temperature=0.75, max_output_tokens=16384)
    enhanced, code = _parse_combined_response(raw_text, prompt)

    report(65, "🔍 Checking the code is complete and valid...")

    # Auto-continue if cut off (bounded retries)
    attempts = 0
    while not is_code_complete(code) and attempts < MAX_CONTINUATIONS:
        attempts += 1
        report(65 + attempts * 10, f"🔧 Code got cut off — adding the missing part (pass {attempts}/{MAX_CONTINUATIONS})...")
        code = code + "\n" + continue_code(code, enhanced, style_desc)
        report(65 + attempts * 10 + 5, "🔍 Re-checking completeness...")

    if not is_code_complete(code):
        report(100, "😕 Still incomplete after retries")
        raise GameGenerationError(
            "The AI generated incomplete or invalid code after several attempts. "
            "Please try again — sometimes a shorter or simpler idea works better."
        )

    report(100, "🎉 Game ready to play!")
    return enhanced, code