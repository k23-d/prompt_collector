import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CATEGORIES = [
    "Marketing", "Sales", "Operations", "Finance",
    "Product", "Customer Support", "HR", "General"
]

def analyze_prompt(prompt_text):
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": (
                    "You are a business strategist and prompt engineer. "
                    "Classify the prompt into one of the following categories: "
                    + ", ".join(CATEGORIES) + ". "
                    "Then suggest a clearer or more effective version of the prompt. "
                    "Respond in this format only:\nCategory: <Category>\nImproved Prompt: <Improved version>"
                )},
                {"role": "user", "content": f"Prompt: {prompt_text}"}
            ],
            temperature=0.3
        )

        output = response.choices[0].message.content.strip()
        print("🔍 GPT Response:", output)

        # Extract category
        category_line = next((line for line in output.splitlines() if line.lower().startswith("category:")), None)
        category = "General"
        if category_line:
            cat_candidate = category_line.split(":", 1)[1].strip()
            if cat_candidate in CATEGORIES:
                category = cat_candidate

        # Extract improved prompt
        improved_prompt_line = next((line for line in output.splitlines() if line.lower().startswith("improved prompt:")), None)
        improved_prompt = prompt_text
        improved = False

        if improved_prompt_line:
            improved_candidate = improved_prompt_line.split(":", 1)[1].strip()
            if improved_candidate and improved_candidate.lower() != prompt_text.lower():
                improved_prompt = improved_candidate
                improved = True

        return {
            "category": category,
            "improved_prompt": improved_prompt,
            "improved": improved
        }

    except Exception as e:
        print("❌ GPT Error:", e)
        return {"category": "General", "improved_prompt": prompt_text, "improved": False}
