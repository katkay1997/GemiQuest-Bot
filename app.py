import streamlit as st
from google import genai
from google.genai import errors
import dotenv
import logging
import os
import random
import time

# 1. Setup
dotenv.load_dotenv()

logger = logging.getLogger("gemiquest")
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

MODEL_ID = "gemini-2.5-flash"
FALLBACK_MODEL_ID = "gemini-2.5-flash-lite"  # Lighter model used if the main one stays unavailable
MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 1.0
SYSTEM_PROMPT = "You are GemiQuest, a creative chatterbox travel guide. Answer with imagination and helpful travel tips!"

# Friendly messages shown in the chat instead of raw API errors
OVERLOADED_MESSAGE = "GemiQuest is a little overwhelmed right now ✨ Try again in a minute!"
QUOTA_MESSAGE = "GemiQuest has used up its travel budget for the moment 🧳 Please wait a bit and try again!"
REQUEST_MESSAGE = "GemiQuest couldn't quite read that map 🗺️ Try rephrasing your question!"
EMPTY_MESSAGE = "GemiQuest got a little lost for words 🌫️ Try asking in a different way!"
ASSISTANT_AVATAR = "assets/travel-icon.png"


class GemiQuestError(Exception):
    """Raised by ask_gemini with a user-friendly message; real details are logged."""

    def __init__(self, user_message):
        super().__init__(user_message)
        self.user_message = user_message


def get_api_key():
    # Prefer Streamlit secrets (.streamlit/secrets.toml or Streamlit Cloud), then environment / .env
    try:
        key = st.secrets.get("API_KEY")
    except Exception:  # No secrets.toml present
        key = None
    return key or os.getenv("API_KEY")


@st.cache_resource
def get_client(api_key):
    return genai.Client(api_key=api_key)


def ask_gemini(contents):
    """Single entry point for all Gemini calls.

    Retries server errors (5xx) with exponential backoff + jitter, then falls back to a
    lighter model. Client errors (4xx) are not retried; 429 quota errors get their own message.
    Returns the response text, or raises GemiQuestError with a friendly message.
    """
    for model in (MODEL_ID, FALLBACK_MODEL_ID):
        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config={'system_instruction': SYSTEM_PROMPT}
                )
            except errors.ServerError as e:
                logger.warning("Gemini server error on %s (attempt %d/%d): %s", model, attempt, MAX_ATTEMPTS, e)
                if attempt < MAX_ATTEMPTS:
                    time.sleep(BASE_DELAY_SECONDS * 2 ** (attempt - 1) + random.uniform(0, 0.5))
                continue
            except errors.ClientError as e:
                if e.code == 429:
                    logger.warning("Gemini quota/rate limit hit on %s: %s", model, e)
                    raise GemiQuestError(QUOTA_MESSAGE) from e
                logger.error("Gemini client error on %s (not retried): %s", model, e)
                raise GemiQuestError(REQUEST_MESSAGE) from e
            except Exception as e:
                logger.exception("Unexpected error calling Gemini on %s", model)
                raise GemiQuestError(OVERLOADED_MESSAGE) from e

            if not response.text:
                logger.warning("Gemini returned no text on %s: %s", model, response)
                raise GemiQuestError(EMPTY_MESSAGE)
            if model != MODEL_ID:
                logger.info("Answered using fallback model %s", model)
            return response.text

        logger.error("Gemini model %s still unavailable after %d attempts", model, MAX_ATTEMPTS)

    raise GemiQuestError(OVERLOADED_MESSAGE)


# Load CSS
try:
    with open("style.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    pass

st.title("GemiQuest ✨")

api_key = get_api_key()
if not api_key:
    logger.error("No API_KEY found in st.secrets or environment variables")
    st.error("GemiQuest can't find its travel pass 🔑 Set API_KEY in .streamlit/secrets.toml or your .env file.")
    st.stop()
client = get_client(api_key)

# 2. Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

# 3. Display Chat History (Above the input so it doesn't flicker)
for message in st.session_state.messages:
    avatar = ASSISTANT_AVATAR if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar):
        st.markdown(message["content"])

# 4. Handle Chat Input
if prompt := st.chat_input("Ask GemiQuest about your next trip!"):
    # Display user message immediately
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 5. Format History for the 1.63.0 SDK
    # We must convert Streamlit's "assistant" role to Gemini's "model" role
    formatted_history = []
    for msg in st.session_state.messages[-6:]:
        formatted_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })

    # 6. Generate Response
    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        try:
            # Use st.spinner so the user knows the bot is working
            with st.spinner("GemiQuest is thinking..."):
                reply = ask_gemini(formatted_history)
            st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        except GemiQuestError as e:
            # Friendly message only; not saved to history so it isn't sent back to Gemini
            st.markdown(e.user_message)
