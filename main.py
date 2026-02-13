# import streamlit as st
# import google.generativeai as genai
# import dotenv
# import os

# dotenv.load_dotenv()

# api_key = os.getenv("API_KEY")
# genai.configure(api_key=api_key)
# model = genai.GenerativeModel("gemini-1.5-flash")

# def response(messages):
#     try:
#         response = model.generate_content(messages)
#         return response
#     except Exception as e:
#         return f"Error:{str(e)}"

# def fetch_conversation_history():
#     if "messages" not in st.session_state:
#         st.session_state["messages"] = [
#             {"role": "user", "parts": "System prompt: You are GemiGenie, a creative chatterbox chatbot who tries to answer questions in a creative way. You will also ask random questions as a conversation starter."}
#         ]
#         return st.session_state["messages"]
# st.title("GemiGenie")

# user_input = st.chat_input("You: ")

# if user_input:
#     messages = fetch_conversation_history()
#     messages.append({"role":"user", "parts": user_input})
#     response = response(messages)
#     messages.append({"role": "model","parts": response.candidates[0].content.parts[0].text})

#     for message in messages:
#         if message["role"] == "model":
#             st.write(f"GemiGenie:{message['parts']}")
#         elif message["role"] == "user" and "System prompt" not in message['parts']:
#             st.write(f"You:{message['parts']}")