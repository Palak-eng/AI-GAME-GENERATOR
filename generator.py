from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)

def generate_game(prompt):
    full_prompt = f"""
You are a Python game developer.

Create a COMPLETE working Pygame game based on this request:
{prompt}

Rules:
- Output ONLY Python code
- Must be complete and runnable
- Must include pygame.init()
- Must include game loop
- No explanations
"""

    response = client.models.generate_content(
        model="models/gemini-2.5-flash",
        contents=full_prompt
    )

    return response.text