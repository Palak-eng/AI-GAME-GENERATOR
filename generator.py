import contextlib
import os
import re
import shutil
import subprocess
import tempfile

from dotenv import load_dotenv
from google import genai

import templates

load_dotenv()

_client: genai.Client | None = None


def _get_api_key() -> str | None:
    # On Streamlit Community Cloud the key comes from Secrets.
    try:
        import streamlit as st

        secret = st.secrets.get("GEMINI_API_KEY")
        if secret:
            return secret
    except Exception:
        pass
    # Locally it comes from the .env file.
    return os.getenv("GEMINI_API_KEY")


# ─── Custom exception for clean error surfacing in the UI ───────────────────


class GameGenerationError(Exception):
    """Raised when prompt enhancement or code generation fails in a known way."""

    pass


def _get_client() -> genai.Client:
    """Lazily initialize the Gemini client so imports don't crash without a key."""
    global _client
    if _client is None:
        api_key = _get_api_key()
        if not api_key:
            raise GameGenerationError(
                "GEMINI_API_KEY is not set.\n\n"
                "Locally: add it to your .env file as GEMINI_API_KEY=your_key_here.\n"
                "On Streamlit Cloud: add it in Settings → Secrets as GEMINI_API_KEY."
            )
        _client = genai.Client(api_key=api_key)
    return _client


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
        response = _get_client().models.generate_content(
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

GAME_DESIGN_RULES = """You are a world-class game designer who makes POLISHED, MAGICAL games for kids.
Before writing any code, design the whole game in your head:
- Keep the kid's core idea the same, but make it EXCITING and HIGH-QUALITY, not a bare prototype
- Add: specific visual details, character descriptions, enemy types, power-ups, background details, color themes, sound mood
- Add: clear win/lose condition, scoring system, difficulty progression
- Design it like a real, finished mobile/arcade game a child would love to play for a long time
- Keep all content suitable for children (no graphic violence or gore, even for "survival" or "zombie" themes — keep it cartoonish and silly)
"""

SYSTEM_PROMPT = """You are a senior HTML5 game developer who makes VISUALLY STUNNING, FINISHED-POLISH browser games
using the Canvas 2D API and vanilla JavaScript. These games are for kids — they must look like a real
published arcade game, and above all they must actually be FUN and WORK CORRECTLY.

════════════════════════════════════════════════
 OVERRIDING PRINCIPLE — CORRECT & CLEAR > FLASHY
════════════════════════════════════════════════
The #1 priority is a game that plays CORRECTLY with clear, obvious controls.
- Every control must be EXPLAINED on screen — a small "controls" hint bar at the bottom
  (e.g. "← → / A D to move · SPACE to shoot") and an on-screen Prompt button/start screen.
- A kid must understand how to play within 5 seconds of seeing it. No hidden mechanics.
- The player character must actually MOVE smoothly (use delta-timed velocity, never fight
  frames). Test the math mentally: collisions, spawns, and restarts must all work logically.
- Every feature you add must be FULLY implemented and actually work. Never stub, never fake it.
  If you say a power-up makes multi-balls, then ACTUALLY create multiple ball objects.
- NO logic bugs: no overlapping colliders, no off-screen spawns, no controls that stop working,
  no restart that doesn't fully reset state.

════════════════════════════════════════════════
 OUTPUT FORMAT — CRITICAL
════════════════════════════════════════════════
- Output ONE complete, self-contained HTML document. Nothing else.
- Structure: <!DOCTYPE html><html>...<head><style>...</style></head><body>
  <canvas id="game" width="800" height="600"></canvas><script>...</script></body></html>
- Everything (CSS + JS) must be INLINE in that one file. No external libraries, no CDN links,
  no external images/fonts/audio files.
- Zero markdown. Zero backticks. Zero explanations before or after the HTML.
- The very last line of your output must be </html>.
- CRITICAL: Code must be 100% complete and runnable. Never stop halfway.

════════════════════════════════════════════════
 SOUND — ADD AUDIO WITH WEB AUDIO API
════════════════════════════════════════════════
Add real sound using the Web Audio API (oscillators / gain envelopes — no external files):
- At least 3 different sounds: e.g. shoot, jump, explosion, coin/pickup, power-up, level-up, game-over
- Small helper functions like playTone(freq, dur, type, vol) using AudioContext + oscillator
- A sound toggle button so kids can mute it (press M or click a speaker icon in the corner)
- Note: browsers block audio until user interaction — initialize the AudioContext on the FIRST
  click/keypress (start button or first input), never at page load.

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
Add moving background details (floating clouds, parallax hills, drifting stars) to feel alive.

RULE 3 — PARTICLES & EFFECTS:
Include at least 3 of these:
  - Explosion particles: on enemy death, spawn 8-12 small circles flying outward, fading over ~0.5s (track particle objects in an array, update + draw each frame)
  - Glow effect: draw the same shape 2-3x with decreasing size/increasing alpha (radial gradient or shadowBlur)
  - Screen flash: on player hit, briefly fill canvas with a semi-transparent red rectangle
  - Trail effect: store the last 5 positions of the player/bullet, draw fading circles along the path
  - Score popup: floating "+100" text that rises and fades when scoring
  - Screen shake: on big events (explosion / hit), offset the canvas briefly

RULE 4 — COLOR PALETTE:
Define at least 8 named color constants (JS consts, hex strings) at the top of the script.
Use jewel tones, neons, or pastels — never just red/green/blue.
Example palettes:
  Neon: #FF00FF, #00FFFF, #FF6600, #00FF66, #FFD700, #FF0055, #0066FF, #CCFF00
  Jewel: #8B00FF, #FF1493, #00CED1, #FFD700, #FF4500, #32CD32, #1E90FF, #FF69B4
  Pastel: #FFB3BA, #FFDFBA, #FFFFBA, #BAFFC9, #BAE1FF, #E8BAFF, #FFBAF3, #BAFFF0

RULE 5 — UI POLISH:
  - Score/lives text: draw shadow first (dark color, +2px offset), then bright text on top
  - A small always-visible "controls" hint bar (e.g. bottom-left corner, faint text)
  - Health bar / lives icon: rounded rect background (dark) + colored fill + white border
  - Game Over screen: semi-transparent dark overlay + big styled text + "Press R or tap to restart" hint

════════════════════════════════
 GAMEPLAY REQUIREMENTS — NON-NEGOTIABLE
════════════════════════════════
◆ CLEAR GOAL & AIM — Every game MUST have one obvious objective the player is
  working toward, and it must be shown on the START screen in plain words,
  e.g. "Collect all 20 gems", "Reach level 10", "Score 500 points to win",
  "Save the friends before time runs out". If you can't state the goal in one
  sentence, redesign it. Never ship an aimless, directionless game.

◆ LEVELS / PROGRESSION — The game MUST have real progression, not endless flat
  play. Use one or more of these:
  - Discrete LEVELS (e.g. complete 5-10 levels that get visibly harder — more
    obstacles, faster enemies, new enemy types — with a "Level X complete!"
    banner and brief pause before the next).
  - Or steady escalating difficulty with clear milestones (e.g. a wave counter,
    "Round 3", difficulty tiers that visibly change the gameplay).
  Each new level/wave should introduce something NEW, not just more of the same.

◆ AIM mentions of controls/menus must never require the SHIFT/CTRL/ALT or letter
  keys that phones lack. It's fine to ALSO support K/M for desktop, but:

◆ TOUCH-FIRST CONTROLS (phones/tablets) — Games MUST be fully playable on
  touch with NO on-screen instructions like "press K". Concretely:
  - On-screen buttons (tap zones) for every action a phone needs: e.g. big
    LEFT / RIGHT arrows and a JUMP/SHOOT/ACTION button drawn on the canvas.
  - OR "tap left half / tap right half / tap-and-hold" style controls that are
    obvious and shown in the hint bar.
  - The START and GAME OVER screens MUST restart by TAPPING — never only a key.
  - The bottom hint bar must be written phone-first: show "◀ ▶ to move · TAP to
    jump", not keyboard-only text.
  Windows/desktop keyboard (arrows/WASD/space) should still work too.

◆ FUN AND IMMEDIATELY PLAYABLE, mouse/touch AND keyboard both work.

◆ CLEAR win/lose condition, a scoring system shown on screen at all times, and
  a HIGH SCORE saved to localStorage.

◆ At least 2 different enemy/obstacle types with different behaviors.

◆ At least 2 power-ups or bonus items with DIFFERENT REAL effects that actually
  work.

◆ Difficulty increases over time OR via levels (enemies get faster, more spawn,
  new enemy types appear).

◆ On Game Over: show "Tap to play again" — TAPPING (or clicking) restarts
  WITHOUT reloading the page (reset ALL game state variables and resume loop).

◆ REPLAYABILITY IS CRITICAL: restart must fully reset score, entities, and
  difficulty so the SAME file can be played again and again with no reload.

◆ Keep all themes child-friendly and cartoonish, even for "survival" or
  "battle" ideas — no realistic violence or gore.

════════════════════════════════
 CODE REQUIREMENTS
════════════════════════════════
- Use requestAnimationFrame for the game loop (not setInterval), and handle ALL input inside the loop
- canvas width=800 height=600, set via the <canvas> tag attributes
- Add a viewport meta tag and a little CSS so the canvas is centered with a dark page background
  (so it looks good full-screen when opened directly)
- document.title should be a short fun name for the game
- No empty function bodies, no placeholder comments — every function fully implemented
- Wrap the game in an IIFE or DOMContentLoaded listener so it runs immediately on file open
- Use delta-time (multiply all movement by dt) so the game runs the same speed on all devices
- Keep the whole game less than ~30KB and organize code with clear sections

ABSOLUTELY FORBIDDEN:
- Single-color rectangles for any game character or enemy
- Solid black/white background with no detail
- Any external script/link/image/font references (must be 100% self-contained, works offline)
- Any non-HTML/CSS/JS text in output
- Incomplete code that cuts off before </html>

════════════════════════════════════════════════
 BROWSER COMPATIBILITY — NEVER LET THE GAME GO BLACK
════════════════════════════════════════════════
- Never call a Canvas API that may be missing on older browsers at a point that
  would crash the whole loop. In particular, DO NOT use context.roundRect() —
  it is not supported everywhere. Draw rounded rectangles manually with
  beginPath + moveTo + arcTo/quadraticCurveTo instead, or wrap any newer API
  call in an `if (ctx.roundRect)` guard / define a small helper fallback.
- Wrap the game loop in try/catch is NOT enough — ensure the FIRST frame cannot
  throw, so the loop always starts and renders something.
- If any browser-specific feature is used, include a tiny inline polyfill fallback.
- The canvas must ALWAYS draw a visible background on frame one — never a black/
  blank screen. Test mentally that draw() runs on every state (including start).
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
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
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
            with contextlib.suppress(OSError):
                os.remove(tmp_path)


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


# Canvas APIs that aren't reliably available on all browsers and would crash the
# game (→ black screen) if called unguarded on the first frame.
_RISKY_CANVAS_APIS = ["roundrect"]


def has_risky_canvas_api(code: str) -> bool:
    """True if the code calls a risky API like roundRect without a guard."""
    lower = code.lower()
    for api in _RISKY_CANVAS_APIS:
        # crude heuristic: presence of the call AND no obvious guard polyfill
        if api in lower and f"if (ctx.{api}" not in lower and f"if (this.ctx.{api}" not in lower:
            return True
    return False


def continue_code(partial_code: str, enhanced_prompt: str, style_desc: str) -> str:
    continuation_prompt = f"""You were writing a self-contained HTML5 Canvas game for: "{enhanced_prompt}" (style: {style_desc})

The HTML/JS below is INCOMPLETE — it got cut off mid-way:

{partial_code}

Continue EXACTLY from where it stopped. Output ONLY the remaining HTML/JS/CSS.
Do NOT repeat anything already written. Start from the cut-off point.
The final lines must properly close the game loop, </script>, </body>, and </html>.
Output ONLY code. No markdown. No explanations."""

    text = _call_model(continuation_prompt, temperature=0.3, max_output_tokens=32768)
    return clean_code(text)


def review_and_fix(code: str, enhanced_prompt: str, style_desc: str) -> str:
    """
    Sends the generated game code back to the model for a self-review pass.
    The model checks for logic bugs, broken controls, non-functional features,
    and unclear UX, then returns a FIXED, complete HTML file. This dramatically
    improves quality over a single-shot generation.

    Returns the improved complete HTML (or the original code if anything fails,
    so the pipeline never hard-fails here).
    """
    review_prompt = f"""You are a quality-control game tester for kids' HTML5 canvas games.
Here is a COMPLETE self-contained HTML5 game:

Game concept: {enhanced_prompt}
Style: {style_desc}

Game code:
<code>
{code}
</code>

Your job: find and fix real bugs that would make a kid confused or frustrated. Focus on:
1. CONTROLS (PHONE-FIRST) — the game must be fully playable on TOUCH: on-screen buttons/tap
   zones or obvious tap-half controls, and NO "press K/letter key" instructions. On-screen
   hint bar must be phone-first (◀ ▶ to move · TAP to jump). Keyboard should also work but never
   be required. Don't use setInterval to read input — read it inside the requestAnimationFrame loop.
2. CLEAR GOAL & LEVELS — there must be ONE obvious objective stated on the START screen, and real
   progression (discrete levels OR escalating waves/difficulty with visible milestones). Add a
   goal line and leveling if missing. A game with no aim and no progression must be fixed.
3. CORRECTNESS — collisions that miss or jitter, off-screen spawns, overlapping colliders,
   a restart that doesn't fully reset, entities that move faster on fast computers.
4. FEATURES THAT ARE FAKED — e.g. a "multi-ball" power-up that doesn't create more balls, or a
   stub function. Make promised features actually work.
5. AUDIO — AudioContext must be created/resumed on the FIRST user interaction (start button /
   first click/keypress), never at page load (browsers block it otherwise).
6. START/END FLOW — a clear Start screen that starts on TAP/click/space, and a Game Over screen
   that fully restarts on TAP/click/R without reloading.
7. BROWSER COMPAT — if the code calls context.roundRect() (or any recent Canvas API) WITHOUT a
   guard/polyfill or manual rounded-rectangle helper, REPLACE it so the game cannot throw on
   older browsers and go black. A black/blank first frame is the #1 killer — make sure draw()
   always paints a visible background in every state.
8. It must play as a coherent, fun, finished game, not a buggy prototype.

Fix any bugs you find. Output the COMPLETE fixed HTML file and ONLY that (the entire
<!DOCTYPE html>...</html>, no extra text, no markdown). If it's already perfect, output the
original code unchanged but still fully complete."""

    try:
        text = _call_model(review_prompt, temperature=0.3, max_output_tokens=32768)
        fixed = clean_code(text)
        if is_code_complete(fixed) and not has_risky_canvas_api(fixed):
            return fixed
    except GameGenerationError:
        pass
    return code


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
        code = clean_code(text[html_start.start() :])
        return (enhanced or f"A fun {fallback_prompt} game, brought to life!"), code

    # Last resort: treat everything as code
    return f"A fun {fallback_prompt} game, brought to life!", clean_code(text)


# ─── Curated template engine ─────────────────────────────────────────────────
# We hand-build a few polished, phone+PC-tested base games. When a kid's idea
# matches one, we RESKIN it with Gemini (only rewrite the THEME VARS + entity
# art), which is far more consistent than inventing a game from scratch.


def pick_template(prompt: str) -> str | None:
    """Return the template key (.e.g 'runner') best matching the idea, or None."""
    text = prompt.lower()
    # collector-ish: grab / collect / items / gems / catch / gather / stars
    if any(
        w in text
        for w in [
            "collect",
            "grab",
            "gather",
            "catch",
            "gem",
            "star",
            "coin",
            "candy",
            "fruit",
            "catch the",
            "pick up",
            "collect the",
            "treasure",
            "berries",
            "fish",
            "catch falling",
        ]
    ):
        return "collector"
    # runner-ish: run / jump / dodge / avoid / obstacle / endless / race / forest
    if any(
        w in text
        for w in [
            "run",
            "runner",
            "jump",
            "dodge",
            "avoid",
            "obstacle",
            "endless",
            "race",
            "forest",
            "desert",
            "skateboard",
            "parkour",
            "speedy",
            "escapes",
            "chase",
        ]
    ):
        return "runner"
    # shooter-ish (checked last so collect/run take priority; requires explicit
    # shoot-action words so generic themes like "space" don't hijack other ideas)
    if any(
        w in text
        for w in [
            "shoot",
            "shooter",
            "blast",
            "laser",
            "shooting",
            "cannon",
            "zap",
            "invader",
            "defend",
            "defense",
        ]
    ):
        return "shooter"
    return None


def _template_by_key(key: str) -> str:
    if key == "collector":
        return templates.COLLECTOR
    if key == "shooter":
        return templates.SHOOTER
    return templates.RUNNER


def _reskin_template(base_code: str, key: str, prompt: str, style_desc: str) -> str:
    """Ask Gemini to reskin a curated template for the kid's idea.

    The model rewrites the THEME VARS (name, colors, player/entity draw
    functions) and the on-screen texts, keeping the proven game logic intact.
    """
    reskin_prompt = f"""You are reskinning a proven, working HTML5 canvas game so it matches a kid's new idea.

Visual style for the reskin: {style_desc}
The kid's idea: {prompt}

The base game below is a "{key}" template. It is CORRECT and fully working — do NOT
change the game logic, physics, collision, scoring, levels, or controls. Only:

1. Rewrite the "THEME VARS" block near the top of the <script>:
   - GAME_NAME → a fun title for this idea
   - THEME colors → fit the new theme and the requested art style
   - Redraw the entity art functions to fit the new characters:
       runner:   drawPlayer / drawObstacle
       collector:drawPlayer / drawItem / drawEnemy
       shooter:  drawPlayer / drawEnemy (keep the enemy type colors in THEME)
     (e.g. for "cat collecting fish", the player becomes a cat shape, the items
     become fish, the enemies become dogs; for "spaceship shoots aliens", the
     player is a ship and the enemies are aliens.)
   Keep each entity drawn with real shapes (arc/lineTo paths), never a plain
   rectangle, and keep the ON-SCREEN controls and hint bar text accurate.
2. Update the start-screen GOAL text and any flavor text to match the theme.
3. Keep it 100% self-contained (no external assets) and keep the exact same
   structure: <!DOCTYPE html> ... </html>, script ends with </script>.
4. Do NOT use ctx.roundRect() (unsupported on some browsers).

Output ONLY the complete reskinned HTML file, no extra text, no markdown, ending in </html>.
Base game to reskin:
<code>
{base_code}
</code>"""

    text = _call_model(reskin_prompt, temperature=0.9, max_output_tokens=16384)
    fixed = clean_code(text)
    if is_code_complete(fixed) and not has_risky_canvas_api(fixed):
        return fixed
    return base_code  # if the reskin failed validation, keep the proven base


def _generate_from_template(prompt: str, key: str, style_desc: str, report) -> tuple[str, str]:
    base = _template_by_key(key)
    report(35, f"🎨 Using the proven {key} base and reskinning it for your idea...")
    code = _reskin_template(base, key, prompt, style_desc)
    if code is base:
        # Reskin failed validation — the known-good base still plays well.
        report(70, "🧐 Reskin had an issue, keeping the polished base version.")
    else:
        report(70, "🔍 Checking the reskinned game is complete and valid...")
        if is_code_complete(code) and not has_risky_canvas_api(code):
            code = review_and_fix(code, prompt, style_desc)
            if is_code_complete(code):
                pass
            else:
                code = base
    report(100, "🎉 Game ready to play!")
    enhanced = _enhanced_blurb(prompt, key)
    return enhanced, code


def _enhanced_blurb(prompt: str, key: str) -> str:
    kind = {
        "runner": "an exciting run-and-jump adventure",
        "collector": "a fun collect-and-dodge quest",
        "shooter": "a fast-paced shoot-and-dodge battle",
    }[key]
    title = prompt.strip()
    # Avoid "A a cute cat" — drop a leading article so the sentence flows.
    title = re.sub(r"^(a|an)\s+", "", title, flags=re.IGNORECASE)
    return f"A {title} game — {kind} with clear goals, rising levels, and big scores. 💫"


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

    # Template path (primary): if the idea matches a proven base game, reskin it
    # for consistency instead of inventing from scratch. Falls back to the full
    # LLM generation below if no template matches.
    template_key = pick_template(prompt)
    if template_key:
        return _generate_from_template(prompt, template_key, style_desc, report)

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
    raw_text = _call_model(full_prompt, temperature=0.75, max_output_tokens=32768)
    enhanced, code = _parse_combined_response(raw_text, prompt)

    report(65, "🔍 Checking the code is complete and valid...")

    # Auto-continue if cut off (bounded retries)
    attempts = 0
    while not is_code_complete(code) and attempts < MAX_CONTINUATIONS:
        attempts += 1
        report(
            65 + attempts * 10,
            f"🔧 Code got cut off — adding the missing part (pass {attempts}/{MAX_CONTINUATIONS})...",
        )
        code = code + "\n" + continue_code(code, enhanced, style_desc)
        report(65 + attempts * 10 + 5, "🔍 Re-checking completeness...")

    if not is_code_complete(code):
        report(100, "😕 Still incomplete after retries")
        raise GameGenerationError(
            "The AI generated incomplete or invalid code after several attempts. "
            "Please try again — sometimes a shorter or simpler idea works better."
        )

    # Self-review pass: send the code back to the model to find & fix bugs
    report(80, "🔬 Quality-checking & fixing bugs... (one more pass)")
    improved = review_and_fix(code, enhanced, style_desc)
    if is_code_complete(improved):
        code = improved

    report(100, "🎉 Game ready to play!")
    return enhanced, code
