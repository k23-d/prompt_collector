from datetime import datetime
from io import BytesIO
import pandas as pd
import os
from dotenv import load_dotenv
from agent_analyzer import analyze_prompt
from dropbox_upload import upload_bytes_to_dropbox
from difflib import SequenceMatcher

load_dotenv()

DROPBOX_PATH = "/PromptCollector/Prompt_Library_Categorized.xlsx"
COLUMNS = ['Prompt', 'Improved Prompt', 'Submitted By', 'Date', 'Tags']

def is_similar(prompt, existing_prompts, threshold=0.7):
    for existing in existing_prompts:
        if SequenceMatcher(None, prompt.lower(), existing.lower()).ratio() >= threshold:
            return True
    return False

def handle_prompt(message_text, user, timestamp):
    improve = "[improve]" in message_text.lower()
    raw_prompt = message_text.replace("#prompt", "").replace("[improve]", "").replace("[raw]", "").strip()

    # Step 1: Classify and improve (if needed)
    if improve:
        analysis = analyze_prompt(raw_prompt)
        improved_prompt = analysis["improved_prompt"]
        category = analysis["category"]
    else:
        improved_prompt = raw_prompt
        category = "General"  # fallback if no GPT categorization
        analysis = analyze_prompt(raw_prompt)
        category = analysis["category"]

    # Step 2: Try to load existing file from Dropbox
    try:
        from dropbox import Dropbox
        import requests

        # Fetch a fresh access token manually
        access_token = requests.post(
            "https://api.dropboxapi.com/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": os.getenv("DROPBOX_REFRESH_TOKEN"),
                "client_id": os.getenv("DROPBOX_APP_KEY"),
                "client_secret": os.getenv("DROPBOX_APP_SECRET"),
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        ).json()["access_token"]

        dbx = Dropbox(oauth2_access_token=access_token)
        metadata, res = dbx.files_download(DROPBOX_PATH)
        excel_file = BytesIO(res.content)
        writer = pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay')
        existing = pd.read_excel(excel_file, sheet_name=None)
    except Exception as e:
        print("📂 Starting fresh Excel file due to error:", e)
        excel_file = BytesIO()
        writer = pd.ExcelWriter(excel_file, engine='openpyxl')
        existing = {}

    # Step 3: Check for similarity
    sheet = category
    df = existing.get(sheet, pd.DataFrame(columns=COLUMNS))
    if is_similar(raw_prompt, df['Prompt'].tolist()):
        return {"status": "similar", "category": category, "prompt": raw_prompt}

    # Step 4: Append to sheet
    ts = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    new_entry = {
        'Prompt': raw_prompt,
        'Improved Prompt': improved_prompt,
        'Submitted By': user,
        'Date': ts,
        'Tags': ''
    }

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(writer, sheet_name=sheet, index=False)
    writer.close()
    upload_bytes_to_dropbox(excel_file, DROPBOX_PATH)

    return {
        "status": "success",
        "category": category,
        "prompt": raw_prompt,
        "improved_prompt": improved_prompt,
        "improved": improve
    }
