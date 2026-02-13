from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("API_KEY")

try:
    client = genai.Client(api_key=api_key)
    print("Testing connection...")
    
    # This list_models call is the ultimate test
    for model in client.models.list():
        print(f"✅ Success! Found model: {model.name}")
        break # Just need to see one to know it works!
        
except Exception as e:
    print(f"❌ API Key Error: {e}")