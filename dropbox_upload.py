import dropbox
import os
from dotenv import load_dotenv

load_dotenv()

def upload_to_dropbox(file_path):
    dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
    dropbox_path = f"/PromptCollector/{file_path}"

    with open(file_path, "rb") as f:
        dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
