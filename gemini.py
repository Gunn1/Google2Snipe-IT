import google.generativeai as genai

from config import Config

# Configure Gemini API
genai.configure(api_key=Config.GEMINI_API_KEY)
model = genai.GenerativeModel(Config.GEMINI_MODEL)


def gemini_prompt(prompt: str):
    """Return the Gemini model response for a given prompt."""
    return model.generate_content(prompt)


if __name__ == "__main__":
    example_prompt = f"""Given the following technology model, Model: Dell Chromebook 11 (3180) select the most appropriate category from this list:
{Config.GEMINI_CATEGORIES}"""
    category_name = gemini_prompt(example_prompt).text
    if "**" in category_name:
        category_name = category_name.split("**")[1].strip()
    print(category_name)
