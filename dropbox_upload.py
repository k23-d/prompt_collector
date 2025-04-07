import os
import requests
from dotenv import load_dotenv
from dropbox import Dropbox
from io import BytesIO

load_dotenv()

DROPBOX_APP_KEY = os.getenv("DROPBOX_APP_KEY")
DROPBOX_APP_SECRET = os.getenv("DROPBOX_APP_SECRET")
DROPBOX_REFRESH_TOKEN = os.getenv("DROPBOX_REFRESH_TOKEN")

def get_fresh_access_token():
    print("🔍 Checking Dropbox credentials:")
    print("APP_KEY starts with:", DROPBOX_APP_KEY[:4])
    print("APP_SECRET starts with:", DROPBOX_APP_SECRET[:4])
    print("REFRESH_TOKEN starts with:", DROPBOX_REFRESH_TOKEN[:8])
    response = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": DROPBOX_REFRESH_TOKEN,
            "client_id": DROPBOX_APP_KEY,
            "client_secret": DROPBOX_APP_SECRET,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    response.raise_for_status()
    return response.json()["access_token"]

def upload_bytes_to_dropbox(file_like_object, dropbox_path):
    try:
        access_token = get_fresh_access_token()
        dbx = Dropbox(oauth2_access_token=access_token)

        file_like_object.seek(0)
        dbx.files_upload(
            file_like_object.read(),
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        print(f"✅ Uploaded to Dropbox: {dropbox_path}")
    except Exception as e:
        print("❌ Dropbox upload failed:", e)
