# AI Game Generator

A Streamlit web app that lets you describe a game idea in plain English and generates a fully playable HTML5 Canvas game using Google Gemini AI.

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up your API key

Get a free Gemini API key at [Google AI Studio](https://aistudio.google.com/apikey), then create a `.env` file:

```
GEMINI_API_KEY=your_key_here
```

Or copy the example:

```bash
cp .env.example .env
# then edit .env with your actual key
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens in your browser. Type a game idea (e.g. "space shooter", "cat jumps over dogs"), pick a style, and hit Generate.

## How It Works

1. You type a simple game idea
2. AI expands it into a detailed game design brief
3. AI generates a complete, self-contained HTML5 Canvas game
4. Play it instantly in the browser
5. Download as a single `.html` file to share or play offline

## Project Structure

```
app.py              # Streamlit frontend (UI, styling, session management)
generator.py        # AI pipeline (prompt enhancement, code generation, validation)
requirements.txt    # Python dependencies
.env.example        # Template for API key setup
```

## Development

### Linting

```bash
ruff check .
ruff format .
```

### Testing

```bash
pytest
```
