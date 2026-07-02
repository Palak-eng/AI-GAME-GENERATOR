from google import genai
from dotenv import load_dotenv
import os
import re
import ast

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
        # Try to surface *why* it was empty (e.g. safety block) if available
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
        raise GameGenerationError(f"Couldn't reach the AI service: {e}") from e
    return _extract_text(response)


def enhance_prompt(user_prompt: str) -> str:
    """Turn a simple kid's idea into a rich game design prompt."""
    return _call_model(
        ENHANCER_PROMPT.format(user_prompt=user_prompt),
        temperature=0.9,
        max_output_tokens=512,
    )


# ─── Game Generator ───────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are a senior Python game developer who makes VISUALLY STUNNING Pygame games.
These games are for kids — they must look colorful, exciting, and polished.

════════════════════════════════════════════════
 GRAPHICS — THIS IS THE MOST IMPORTANT SECTION
════════════════════════════════════════════════

RULE 1 — NO PLAIN RECTANGLES FOR CHARACTERS:
Every character, enemy, player, boss, power-up MUST be drawn with at least 3-4 pygame.draw calls combined.
Examples of what a player can look like:
  - Spaceship: triangle body (polygon) + 2 small wing triangles + circle cockpit + engine glow circle
  - Character: circle head + rounded body (ellipse) + 2 line arms + 2 line legs
  - Animal: large circle body + small circle head + triangle ears + dot eyes

RULE 2 — RICH BACKGROUNDS (never solid black or white):
Choose ONE of these background styles and implement it fully:
  Option A — Gradient: draw 600 horizontal lines, color interpolated from top_color to bottom_color
  Option B — Starfield: 150 random white/yellow dots of varying sizes (1-3px) scattered across screen
  Option C — Tiled pattern: draw repeating shapes (clouds, bricks, grass tiles, hex grid) across screen
  Option D — Layered parallax: 2-3 layers of simple shapes scrolling at different speeds

RULE 3 — PARTICLES & EFFECTS:
You MUST include at least 2 of these effects:
  - Explosion particles: on enemy death, spawn 8-12 small circles flying outward, fading over 0.5s
  - Glow effect: draw same shape 3x in decreasing size, lightest color first (outer glow → bright center)
  - Screen flash: on player hit, briefly fill screen with semi-transparent red overlay (alpha surface)
  - Trail effect: store last 5 positions of player/bullet, draw fading circles along the path
  - Score popup: floating "+100" text that rises and fades when scoring

RULE 4 — COLOR PALETTE:
Define at least 8 named color constants at the top. Use jewel tones, neons, or pastels — never just red/green/blue.
Example palettes:
  Neon: #FF00FF, #00FFFF, #FF6600, #00FF66, #FFD700, #FF0055, #0066FF, #CCFF00
  Jewel: #8B00FF, #FF1493, #00CED1, #FFD700, #FF4500, #32CD32, #1E90FF, #FF69B4
  Pastel: #FFB3BA, #FFDFBA, #FFFFBA, #BAFFC9, #BAE1FF, #E8BAFF, #FFBAF3, #BAFFF0

RULE 5 — UI POLISH:
  - Score/lives text: draw shadow first (dark color, +2px offset), then bright text on top
  - Health bar: rounded rect background (dark) + colored fill + white border
  - Game Over screen: semi-transparent dark overlay + big styled text + "Press R to restart" hint

════════════════════════════════
 GAMEPLAY REQUIREMENTS
════════════════════════════════
- Fun and immediately playable by a child
- Scoring system shown on screen at all times
- Clear win condition OR survive-as-long-as-possible with high score
- At least 2 different enemy/obstacle types with different behaviors
- At least 1 power-up or bonus item
- Controls: arrow keys or WASD, SPACE to shoot/jump
- Difficulty increases over time (enemies get faster, more spawn, etc.)
- "Press R to restart" after Game Over
- Keep all themes child-friendly and cartoonish, even for "survival" or "battle" ideas — no realistic violence or gore

════════════════════════════════
 CODE REQUIREMENTS
════════════════════════════════
- Output ONLY raw Python code. Zero markdown. Zero backticks. Zero explanations.
- First lines must be: import pygame, import sys, import random, import math
- Call pygame.init() early, set caption with pygame.display.set_caption()
- 60 FPS with clock.tick(60)
- Window: 800x600
- CRITICAL: Code must be 100% complete. Must end with the running game loop. Never stop halfway.
- No empty function bodies. No placeholder comments like "# draw enemy here".

ABSOLUTELY FORBIDDEN:
- Single-color rectangles for any game character or enemy
- Solid black/white background with no detail
- Any non-Python text in output
- Incomplete code that cuts off
"""

MAX_CONTINUATIONS = 2


def clean_code(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\n", "", text)
    text = re.sub(r"\n```$", "", text)
    text = re.sub(r"```[a-zA-Z]*", "", text)
    text = re.sub(r"```", "", text)
    return text.strip()


def is_code_complete(code: str) -> bool:
    """
    Heuristic completeness check. Also verifies the code actually parses as
    valid Python — substring checks alone can be fooled by comments/strings.
    """
    has_loop = "clock.tick" in code or "pygame.quit" in code
    has_flip = "pygame.display.flip" in code or "pygame.display.update" in code
    if not (has_loop and has_flip):
        return False
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def continue_code(partial_code: str, enhanced_prompt: str, style_desc: str) -> str:
    continuation_prompt = f"""You were writing a Pygame game for: "{enhanced_prompt}" (style: {style_desc})

The code below is INCOMPLETE — it got cut off mid-way:

{partial_code}

Continue EXACTLY from where it stopped. Output ONLY the remaining Python code.
Do NOT repeat anything already written. Start from the cut-off point.
The final lines must be the running game loop with clock.tick(60) and pygame.display.flip().
Output ONLY Python code. No markdown. No explanations."""

    text = _call_model(continuation_prompt, temperature=0.3, max_output_tokens=8192)
    return clean_code(text)


def generate_game(prompt: str, style: str = "arcade") -> tuple[str, str]:
    """
    Returns (enhanced_prompt, game_code) so the UI can show what was improved.
    Raises GameGenerationError on any failure, with a user-safe message.
    """
    style_hints = {
        "arcade": "Classic arcade — vibrant neon colors, dark background, fast action.",
        "retro": "16-bit retro — punchy limited palette, pixel-art inspired shapes.",
        "space": "Space adventure — starfield background, glowing ships, laser beams.",
        "fantasy": "Fantasy RPG — jewel tone palette, magical glowing particles, rich scenery.",
        "minimal": "Clean minimal — white/pastel background, bold geometric shapes, smooth animation.",
    }
    style_desc = style_hints.get(style, style_hints["arcade"])

    # Step 1: Enhance the kid's prompt
    enhanced = enhance_prompt(prompt)

    # Step 2: Build full generation prompt
    full_prompt = f"""{SYSTEM_PROMPT}

Visual style: {style_desc}

Game design brief:
{enhanced}

IMPORTANT: Write the ENTIRE complete game right now. Do not stop early.
The very last line of your output must be inside the running game loop.

Begin the Python code now:"""

    raw_text = _call_model(full_prompt, temperature=0.7, max_output_tokens=16384)
    code = clean_code(raw_text)

    # Step 3: Auto-continue if cut off (bounded retries)
    attempts = 0
    while not is_code_complete(code) and attempts < MAX_CONTINUATIONS:
        code = code + "\n" + continue_code(code, enhanced, style_desc)
        attempts += 1

    if not is_code_complete(code):
        raise GameGenerationError(
            "The AI generated incomplete or invalid code after several attempts. "
            "Please try again — sometimes a shorter or simpler idea works better."
        )

    return enhanced, code