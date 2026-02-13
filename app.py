import streamlit as st
from google import genai
import dotenv
import os

# 1. Setup
dotenv.load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

MODEL_ID = "gemini-2.5-flash"
SYSTEM_PROMPT = "You are GemiQuest, a creative chatterbox travel guide. Answer with imagination and helpful travel tips!"

# Load CSS
try:
    with open("style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("GemiQuest ✨")

# 2. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display Chat History (Above the input so it doesn't flicker)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 4. Handle Chat Input
if prompt := st.chat_input("Ask GemiQuest about your next trip!"):
    # Display user message immediately
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5. Format History for the 1.63.0 SDK
    # We must convert Streamlit's "assistant" role to Gemini's "model" role
    formatted_history = []
    for msg in st.session_state.messages:
        formatted_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}] # Strict requirement: list of dicts
        })

    # 6. Generate Response
    try:
        # Use st.spinner so the user knows the bot is working
        with st.spinner("GemiQuest is thinking..."):
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=formatted_history,
                config={'system_instruction': SYSTEM_PROMPT}
            )
        
        # Display and save response
        with st.chat_message("assistant"):
            st.markdown(response.text)
        st.session_state.messages.append({"role": "assistant", "content": response.text})

    except Exception as e:
        st.error(f"GemiQuest hit a snag: {e}")


# import streamlit as st
# from google import genai  # Modern import
# import dotenv
# import os

# # 1. Configuration
# dotenv.load_dotenv()
# api_key = os.getenv("API_KEY")
# client = genai.Client(api_key=api_key)

# # Model and Personality
# MODEL_ID = "gemini-1.5-flash"
# SYSTEM_PROMPT = (
#     "You are GemiQuest, a creative travel chatbot. "
#     "Be imaginative, suggest affordable travel, and give tips for trips. "
#     "Always stay in character as a helpful, chatterbox travel guide!"
# )

# # Load CSS
# try:
#     with open("style.css", "r") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
# except FileNotFoundError:
#     pass

# st.title("GemiQuest ✈️")

# # 2. Initialize Session State
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # 3. Display Chat History
# for message in st.session_state.messages:
#     with st.chat_message(message["role"]):
#         st.markdown(message["content"])

# # 4. Handle User Input
# if prompt := st.chat_input("Ask GemiQuest about your next adventure!"):
#     # Display user message
#     st.chat_message("user").markdown(prompt)
    
#     # Add to history
#     st.session_state.messages.append({"role": "user", "content": prompt})

#     # 5. Generate Response
#     try:
#         # The new SDK passes system instructions in the config
#         response = client.models.generate_content(
#             model=MODEL_ID,
#             contents=st.session_state.messages, # Pass the whole list for context
#             config={'system_instruction': SYSTEM_PROMPT}
#         )
        
#         response_text = response.text

#         # Display and save assistant response
#         with st.chat_message("assistant"):
#             st.markdown(response_text)
#         st.session_state.messages.append({"role": "assistant", "content": response_text})

#     except Exception as e:
#         st.error(f"GemiQuest hit a snag: {e}")









