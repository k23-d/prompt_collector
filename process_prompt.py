import pandas as pd
from datetime import datetime
from dropbox_upload import upload_to_dropbox

EXCEL_FILE = "Prompt_Library.xlsx"

def handle_prompt(prompt, user, timestamp):
    ts = datetime.fromtimestamp(float(timestamp)).strftime('%Y-%m-%d %H:%M:%S')
    data = {'Prompt': prompt, 'Submitted By': user, 'Date': ts, 'Tags': ''}

    try:
        df = pd.read_excel(EXCEL_FILE)
    except FileNotFoundError:
        df = pd.DataFrame(columns=['Prompt', 'Submitted By', 'Date', 'Tags'])

    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(EXCEL_FILE, index=False)

    upload_to_dropbox(EXCEL_FILE)
