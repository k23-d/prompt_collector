from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
from process_prompt import handle_prompt

load_dotenv()
app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("message")
def handle_message_events(body, say, client):
    event = body.get("event", {})
    text = event.get("text", "")
    user = event.get("user", "")
    ts = event.get("ts", "")
    channel = event.get("channel", "")

    if '#prompt' in text or '✅' in text:
        result = handle_prompt(text, user, ts)
        if result['status'] == "success":
            client.chat_postMessage(channel=channel, thread_ts=ts,
                                    text=f"✅ Prompt saved under *{result['category']}*!")
        elif result['status'] == "duplicate":
            client.chat_postMessage(channel=channel, thread_ts=ts,
                                    text=f"⚠️ Duplicate prompt — already stored under *{result['category']}*.")
        else:
            client.chat_postMessage(channel=channel, thread_ts=ts,
                                    text="❌ Error saving your prompt. Please try again.")

if __name__ == "__main__":
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
