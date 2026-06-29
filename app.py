import streamlit as st
from generator import generate_game

st.set_page_config(page_title="AI Game Generator", layout="centered")

st.title("🎮 AI Game Generator")
st.write("Type a game idea and AI will build a Pygame game for you")

user_prompt = st.text_input("Enter your game idea:", placeholder="e.g. space shooter game with enemies and bullets")

if st.button("Generate Game 🚀"):
    if user_prompt:
        with st.spinner("Generating game..."):
            code = generate_game(user_prompt)

            # show code
            st.subheader("Generated Code")
            st.code(code, language="python")

            # save file
            with open("generated_games/game.py", "w", encoding="utf-8") as f:
                f.write(code)

            st.success("Game generated and saved in generated_games/game.py")
    else:
        st.warning("Please enter a prompt")