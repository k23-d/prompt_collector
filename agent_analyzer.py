#AI Agent

import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

CATEGORIES = [
    "Marketing", "Sales", "Operations", "Finance",
    "Product", "Customer Support", "HR", "General"
]

def analyze_prompt(prompt_text):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": (
                    "You are a business strategist and prompt engineer. "
                    "Classify the prompt into one of the following categories: "
                    + ", ".join(CATEGORIES) + ". "
                    "Then suggest a clearer or more effective version if possible."
                )},
                {"role": "user", "content": f"Prompt: {prompt_text}"}
            ],
            temperature=0.3
        )

        output = response.choices[0].message.content.strip()
        category = next((cat for cat in CATEGORIES if cat.lower() in output.lower()), "General")

        improved_prompt = prompt_text
        if "Improved Prompt:" in output:
            improved_prompt = output.split("Improved Prompt:")[1].strip()
        elif "Improved version:" in output:
            improved_prompt = output.split("Improved version:")[1].strip()

        return {"category": category, "improved_prompt": improved_prompt}
    except Exception as e:
        print("❌ GPT Error:", e)
        return {"category": "General", "improved_prompt": prompt_text}
