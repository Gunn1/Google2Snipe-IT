from dotenv import load_dotenv
import os
import google.generativeai as genai


# Load environment variables from .env file
load_dotenv()

# Access the variable
api_key = os.getenv("Gemini_APIKEY") 
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")


def gemini_prompt(prompt: str):
    """Return the Gemini model response for a given prompt."""
    return model.generate_content(prompt)


if __name__ == "__main__":
    example_prompt = (
        """Given the following technology model,Model: Dell Chromebook 11 (3180) select the most appropriate category from this list:
IMac,Tablets,Mobile Devices,Servers,Networking Equipment,Printers & Scanners,Desktop,Chromebook"""
    )
    category_name = gemini_prompt(example_prompt).text
    if "**" in category_name:
        category_name = category_name.split("**")[1].strip()
    print(category_name)
