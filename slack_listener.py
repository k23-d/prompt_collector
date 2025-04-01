from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import os
from dotenv import load_dotenv
from process_prompt import handle_prompt

load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("message")
def handle_message_events(body, say):
    text = body.get('event', {}).get('text', '')
    if '#prompt' in text or '✅' in text:
        user = body['event']['user']
        timestamp = body['event']['ts']
        handle_prompt(text, user, timestamp)

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
