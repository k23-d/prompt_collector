from datetime import datetime
from io import BytesIO
import pandas as pd
import os
from dotenv import load_dotenv
from agent_analyzer import analyze_prompt
from dropbox_upload import upload_bytes_to_dropbox
from difflib import SequenceMatcher
from openpyxl import Workbook, load_workbook
from dropbox import Dropbox
import requests

load_dotenv()

DROPBOX_PATH = "/PromptCollector/Prompt_Library_Categorized.xlsx"

DEFAULT_COLUMNS = ['Prompt', 'Improved Prompt', 'Submitted By', 'Date', 'Tags']
ACTIONABLE_COLUMNS = ['Prompt', 'Improved Prompt', 'Submitted By', 'Date', 'Business Function', 'Status', 'Tags']

def is_similar(prompt, existing_prompts, threshold=0.7):
    for existing in existing_prompts:
        if SequenceMatcher(None, prompt.lower(), existing.lower()).ratio() >= threshold:
            return True
    return False

def handle_prompt(message_text, user, timestamp):
    improve = "[improve]" in message_text.lower()
    is_actionable = "[action]" in message_text.lower()

    raw_prompt = (
        message_text
        .replace("#prompt", "")
        .replace("[improve]", "")
        .replace("[action]", "")
        .replace("[raw]", "")
        .strip()
    )

    # GPT analysis runs regardless, to classify business function
    analysis = analyze_prompt(raw_prompt)
    improved_prompt = analysis["improved_prompt"] if improve else raw_prompt
    category = analysis["category"]

    # Select the correct sheet and columns
    sheet = "Actionable_Prompts" if is_actionable else category
    columns = ACTIONABLE_COLUMNS if is_actionable else DEFAULT_COLUMNS

    ts = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

    # Prepare the new entry depending on whether it’s actionable
    new_entry = {
        'Prompt': raw_prompt,
        'Improved Prompt': improved_prompt,
        'Submitted By': user,
        'Date': ts,
        'Tags': ''
    }
    if is_actionable:
        new_entry['Business Function'] = category
        new_entry['Status'] = 'Pending'

    # Refresh Dropbox access token
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

    existing_sheets = {}
    try:
        metadata, res = dbx.files_download(DROPBOX_PATH)
        input_excel = BytesIO(res.content)
        existing_sheets = pd.read_excel(input_excel, sheet_name=None)
    except Exception as e:
        print("📂 No existing file or unreadable. Creating new workbook.", e)

    df_existing = existing_sheets.get(sheet, pd.DataFrame(columns=columns))

    if is_similar(raw_prompt, df_existing['Prompt'].tolist()):
        return {"status": "similar", "category": category, "prompt": raw_prompt}

    df_updated = pd.concat([df_existing, pd.DataFrame([new_entry])], ignore_index=True)

    # Create a new in-memory Excel file and write all sheets (including updated one)
    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        for sheet_name, dataframe in existing_sheets.items():
            if sheet_name != sheet:
                dataframe.to_excel(writer, sheet_name=sheet_name, index=False)
        df_updated.to_excel(writer, sheet_name=sheet, index=False)

    output_excel.seek(0)
    upload_bytes_to_dropbox(output_excel, DROPBOX_PATH)

    return {
        "status": "success",
        "category": category,
        "prompt": raw_prompt,
        "improved_prompt": improved_prompt,
        "improved": improve,
        "actionable": is_actionable
    }
