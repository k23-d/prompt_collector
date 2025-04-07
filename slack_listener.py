from datetime import datetime
from io import BytesIO
import pandas as pd
import dropbox
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
        analysis = analyze_prompt(raw_prompt)  # still classify for sheet routing
        category = analysis["category"]

    # Step 2: Download current file from Dropbox
    try:
        dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
        metadata, res = dbx.files_download(DROPBOX_PATH)
        excel_file = BytesIO(res.content)
        writer = pd.ExcelWriter(excel_file, engine='openpyxl', mode='a', if_sheet_exists='overlay')
        existing = pd.read_excel(excel_file, sheet_name=None)
    except dropbox.exceptions.ApiError:
        excel_file = BytesIO()
        writer = pd.ExcelWriter(excel_file, engine='openpyxl')
        existing = {}

    # Step 3: Check for similarity
    sheet = category
    df = existing.get(sheet, pd.DataFrame(columns=COLUMNS))
    if is_similar(raw_prompt, df['Prompt'].tolist()):
        return {"status": "similar", "category": category, "prompt": raw_prompt}

    # Step 4: Append to the correct sheet
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
