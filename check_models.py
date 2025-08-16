import google.generativeai as genai
import os

# --- CONFIGURATION ---
# Replace with your key or set it as an environment variable
GEMINI_API_KEY = 'AIzaSyBydEqVQL13gqviRdqrbV9cdReCSFDbFUk' 

genai.configure(api_key=GEMINI_API_KEY)

print("Available Gemini Models:")
for m in genai.list_models():
  # The 'generateContent' method is what our script uses.
  if 'generateContent' in m.supported_generation_methods:
    print(f"- {m.name}")