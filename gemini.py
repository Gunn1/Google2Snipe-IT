from dotenv import load_dotenv
import os
import google.generativeai as genai


# Load environment variables from .env file
load_dotenv()

# Access the variable
api_key = os.getenv("Gemini_APIKEY") 
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")
def gemini_prompt(prompt):
    response = model.generate_content(prompt)
    return response

category_name = gemini_prompt("""Given the following technology model,Model: Dell Chromebook 11 (3180) select the most appropriate category from this list:
IMac,Tablets,Mobile Devices,Servers,Networking Equipment,Printers & Scanners,Desktop,Chromebook
""").text
category_name = category_name.split('**')[1]
print(category_name)