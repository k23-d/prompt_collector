import pandas as pd
from dropbox_upload import download_excel_from_dropbox, upload_bytes_to_dropbox
from io import BytesIO

DROPBOX_PATH = "/PromptCollector/Prompt_Library_Categorized.xlsx"

def fetch_actionable_prompts():
    workbook = download_excel_from_dropbox(DROPBOX_PATH)
    df = pd.read_excel(workbook, sheet_name="Actionable_Prompts")
    df = df[df.get("Status", "Pending") != "Executed"]  # Filter out executed prompts
    return df.reset_index().to_dict(orient="records")

def format_prompt_list(prompts):
    return "\n".join([f"{idx+1}. {p['Prompt']} (Function: {p.get('Business Function', 'N/A')})"
                      for idx, p in enumerate(prompts)])

def fetch_prompt_by_id(prompt_id):
    prompts = fetch_actionable_prompts()
    if 0 < prompt_id <= len(prompts):
        return prompts[prompt_id - 1]
    return None

def update_prompt_status(prompt_id, status):
    workbook = download_excel_from_dropbox(DROPBOX_PATH)
    df = pd.read_excel(workbook, sheet_name="Actionable_Prompts")
    if 0 < prompt_id <= len(df):
        df.loc[prompt_id - 1, "Status"] = status
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Actionable_Prompts", index=False)
    output.seek(0)
    upload_bytes_to_dropbox(output, DROPBOX_PATH)
