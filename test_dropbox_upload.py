from io import BytesIO
from dropbox_upload import upload_bytes_to_dropbox

test_file = BytesIO()
test_file.write(b"This is a test file sent from Railway!")
upload_bytes_to_dropbox(test_file, "/PromptCollector/Test_Upload.txt")
