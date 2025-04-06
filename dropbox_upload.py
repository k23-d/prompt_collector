import dropbox
import os
from dotenv import load_dotenv

load_dotenv()

def upload_bytes_to_dropbox(file_like_object, path):
    file_like_object.seek(0)
    dbx = dropbox.Dropbox(os.getenv("DROPBOX_ACCESS_TOKEN"))
    dbx.files_upload(file_like_object.read(), path, mode=dropbox.files.WriteMode.overwrite)
