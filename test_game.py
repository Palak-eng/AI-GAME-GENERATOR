import subprocess
import sys
import os

def run_game(path: str = "generated_games/game.py"):
    if not os.path.exists(path):
        print(f"Error: {path} not found. Generate a game first.")
        sys.exit(1)
    print(f"Launching {path} ...")
    subprocess.run([sys.executable, path])

if __name__ == "__main__":
    game_path = sys.argv[1] if len(sys.argv) > 1 else "generated_games/game.py"
    run_game(game_path)