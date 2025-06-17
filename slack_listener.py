from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from dotenv import load_dotenv
import os
from process_prompt import handle_prompt

load_dotenv()

app = App(token=os.getenv("SLACK_BOT_TOKEN"))

@app.event("message")
def handle_message_events(body, say, client):
    try:
        event = body.get("event", {})
        text = event.get("text", "")
        user = event.get("user", "")
        ts = event.get("ts", "")
        channel = event.get("channel", "")
        print("📥 message detected:", text)

        if "#prompt" in text.lower():
            print("📥 Prompt detected:", text)
            result = handle_prompt(text, user, ts)

            # 📣 Generate Slack reply based on result
            if result["status"] == "success":
                if result["improved"]:
                    reply = (
                        f"✅ *Prompt saved under* `{result['category']}` with improvements!\n\n"
                        f"*Improved Prompt:* {result['improved_prompt']}"
                    )
                else:
                    reply = (
                        f"✅ *Prompt saved under* `{result['category']}` as-is.\n"
                        f"_No improvements were suggested by the AI._"
                    )
            elif result["status"] == "similar":
                reply = (
                    f"⚠️ A similar prompt already exists in `{result['category']}`.\n"
                    f"_This one was not saved to avoid duplication._"
                )
            else:
                reply = "❌ Something went wrong while processing your prompt. Please try again."

            # ✅ Reply to the original message in thread
            client.chat_postMessage(channel=channel, thread_ts=ts, text=reply)

        else:
            print("ℹ️ Message ignored (no #prompt tag).")

    except Exception as e:
        print("❌ Slack bot error:", e)
        client.chat_postMessage(
            channel=channel,
            thread_ts=ts,
            text="🚨 Something went wrong while processing your prompt. Please contact the admin."
        )

if __name__ == "__main__":
    print("🚀 Starting Prompt Collector Slack Bot...")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
