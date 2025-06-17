import os
import requests
from dropbox import Dropbox
from dropbox.files import WriteMode

print("🧪 DEBUG: Dumping environment keys from Railway...")
for k, v in os.environ.items():
    if "DROPBOX" in k:
        print(f"{k} = {v[:6]}... (len: {len(v)})")
        
def get_fresh_access_token():
    app_key = os.getenv("DROPBOX_APP_KEY")
    app_secret = os.getenv("DROPBOX_APP_SECRET")
    refresh_token = os.getenv("DROPBOX_REFRESH_TOKEN")

    if not app_key or not app_secret or not refresh_token:
        raise ValueError("❌ Dropbox auth variables not loaded")

    print("🔑 Generating fresh Dropbox access token...")

    response = requests.post(
        "https://api.dropboxapi.com/oauth2/token",
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": app_key,
            "client_secret": app_secret,
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    response.raise_for_status()
    token = response.json()["access_token"]
    print("✅ Access token received (len: {})".format(len(token)))
    return token

def upload_bytes_to_dropbox(file_like_object, dropbox_path):
    try:
        access_token = get_fresh_access_token()
        dbx = Dropbox(oauth2_access_token=access_token)

        file_like_object.seek(0)
        dbx.files_upload(
            file_like_object.read(),
            dropbox_path,
            mode=WriteMode.overwrite
        )
        print(f"✅ Uploaded to Dropbox: {dropbox_path}")
    except Exception as e:
        print("❌ Dropbox upload failed:", e)
