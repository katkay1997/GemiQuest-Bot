import streamlit as st
from google import genai
import dotenv
import os
import pandas as pd

# -------------------------
# 1. Setup
# -------------------------
dotenv.load_dotenv()
api_key = os.getenv("API_KEY")
client = genai.Client(api_key=api_key)

MODEL_ID = "gemini-2.5-flash"

SYSTEM_PROMPT = """
You are an AI data assistant specializing in NYC housing and education.
Use provided dataset summaries to answer accurately.
Reference metrics when possible.
Be analytical and concise.
"""

# -------------------------
# 2. Load Data (Cached)
# -------------------------
@st.cache_data
def load_data():
    housing = pd.read_csv("housing.csv")
    education = pd.read_csv("education.csv")
    return housing, education

housing_df, education_df = load_data()

# -------------------------
# 3. Intent Detection
# -------------------------
def detect_intent(prompt):
    p = prompt.lower()
    if "rent" in p or "housing" in p or "eviction" in p:
        return "housing"
    elif "graduation" in p or "school" in p or "education" in p:
        return "education"
    elif "compare" in p or "correlation" in p:
        return "analysis"
    return "general"

# -------------------------
# 4. UI Setup
# -------------------------
st.title("NYC Education & Housing Data Assistant 📊")

mode = st.sidebar.selectbox(
    "Select Mode",
    ["General Chat", "Data Analysis Mode"]
)

st.sidebar.markdown("### Data Sources")
st.sidebar.markdown("- NYC Housing Dataset")
st.sidebar.markdown("- NYC Education Dataset")

# -------------------------
# 5. Session State
# -------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# -------------------------
# 6. Chat Input
# -------------------------
if prompt := st.chat_input("Ask about NYC housing or education trends..."):

    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    intent = detect_intent(prompt)

    # -------------------------
    # 7. Data Retrieval Layer
    # -------------------------
    summary = ""

    if mode == "Data Analysis Mode":

        if intent == "housing":
            summary = housing_df.describe().to_string()

        elif intent == "education":
            summary = education_df.describe().to_string()

        elif intent == "analysis":
            merged = pd.merge(
                housing_df,
                education_df,
                on="District",  # Make sure this column exists in both
                how="inner"
            )
            summary = merged.describe().to_string()

        else:
            summary = "No relevant dataset identified."

    # -------------------------
    # 8. Format History for Gemini
    # -------------------------
    formatted_history = []

    for msg in st.session_state.messages[-6:]:
        formatted_history.append({
            "role": "user" if msg["role"] == "user" else "model",
            "parts": [{"text": msg["content"]}]
        })

    augmented_prompt = f"""
User question:
{prompt}

Relevant dataset summary:
{summary}

Answer using the dataset information above when applicable.
"""

    formatted_history.append({
        "role": "user",
        "parts": [{"text": augmented_prompt}]
    })

    # -------------------------
    # 9. Generate Response
    # -------------------------
    try:
        with st.spinner("Analyzing data..."):
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=formatted_history,
                config={'system_instruction': SYSTEM_PROMPT}
            )

        with st.chat_message("assistant"):
            st.markdown(response.text)

        st.session_state.messages.append({
            "role": "assistant",
            "content": response.text
        })

        # -------------------------
        # 10. Optional Visualization
        # -------------------------
        if mode == "Data Analysis Mode":

            if intent == "housing" and "RentBurden" in housing_df.columns:
                st.subheader("Housing Data Snapshot")
                st.bar_chart(housing_df["RentBurden"])

            elif intent == "education" and "GraduationRate" in education_df.columns:
                st.subheader("Education Data Snapshot")
                st.bar_chart(education_df["GraduationRate"])

    except Exception as e:
        st.error(f"Error: {e}")