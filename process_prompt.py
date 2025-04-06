from datetime import datetime
from io import BytesIO
import pandas as pd
import dropbox
import os
from dotenv import load_dotenv
from agent_analyzer import analyze_prompt
from dropbox_upload import upload_bytes_to_dropbox

load_dotenv()

DROPBOX_PATH = "/PromptCollector/Prompt_Library_Categorized.xlsx"
COLUMNS = ['Prompt', 'Improved Prompt', 'Submitted By', 'Date', 'Tags']

def handle_prompt(prompt, user, timestamp):
    analyzed = analyze_prompt(prompt)
    category = analyzed['category']
    improved = analyzed['improved_prompt']

    ts = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    new_entry = {'Prompt': prompt, 'Improved Prompt': improved, 'Submitted By': user, 'Date': ts, 'Tags': ''}

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

    sheet = category
    df = existing.get(sheet, pd.DataFrame(columns=COLUMNS))
    if not df[df['Prompt'] == prompt].empty:
        return {"status": "duplicate", "category": category}

    df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
    df.to_excel(writer, sheet_name=sheet, index=False)
    writer.close()
    upload_bytes_to_dropbox(excel_file, DROPBOX_PATH)
    return {"status": "success", "category": category}
