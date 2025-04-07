from datetime import datetime
from io import BytesIO
import pandas as pd
import os
from dotenv import load_dotenv
from agent_analyzer import analyze_prompt
from dropbox_upload import upload_bytes_to_dropbox
from difflib import SequenceMatcher
from openpyxl import load_workbook

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

    if improve:
        analysis = analyze_prompt(raw_prompt)
        improved_prompt = analysis["improved_prompt"]
        category = analysis["category"]
    else:
        improved_prompt = raw_prompt
        analysis = analyze_prompt(raw_prompt)
        category = analysis["category"]

    sheet = category
    ts = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    new_entry = {
        'Prompt': raw_prompt,
        'Improved Prompt': improved_prompt,
        'Submitted By': user,
        'Date': ts,
        'Tags': ''
    }

    from dropbox import Dropbox
    import requests

    try:
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
        input_excel = BytesIO(res.content)
        wb = load_workbook(input_excel)
        existing_sheets = wb.sheetnames
    except Exception as e:
        print("📂 No existing file, creating new workbook.", e)
        wb = None
        existing_sheets = []

    output = BytesIO()
    if wb:
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            writer.book = wb
            writer.sheets = {ws.title: ws for ws in wb.worksheets}

            if sheet in wb.sheetnames:
                df_existing = pd.read_excel(input_excel, sheet_name=sheet)
            else:
                df_existing = pd.DataFrame(columns=COLUMNS)

            if is_similar(raw_prompt, df_existing['Prompt'].tolist()):
                return {"status": "similar", "category": category, "prompt": raw_prompt}

            df_updated = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)
            df_updated.to_excel(writer, sheet_name=sheet, index=False)
    else:
        df = pd.DataFrame([new_entry])
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet, index=False)

    output.seek(0)
    upload_bytes_to_dropbox(output, DROPBOX_PATH)

    return {
        "status": "success",
        "category": category,
        "prompt": raw_prompt,
        "improved_prompt": improved_prompt,
        "improved": improve
    }
