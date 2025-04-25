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

@app.command("/list_prompts")
def list_prompts(ack, say):
    ack()
    from actionable_prompts import fetch_actionable_prompts, format_prompt_list
    prompts = fetch_actionable_prompts()
    if not prompts:
        say("There are no actionable prompts available.")
    else:
        say(format_prompt_list(prompts))

@app.command("/run_prompt")
def run_prompt(ack, say, command):
    ack()
    prompt_id_text = command["text"].strip()
    if not prompt_id_text.isdigit():
        say("Please provide a valid numeric Prompt ID.")
        return

    prompt_id = int(prompt_id_text)
    from actionable_prompts import fetch_prompt_by_id, update_prompt_status
    from gpt_runner import execute_prompt_with_gpt

    prompt_data = fetch_prompt_by_id(prompt_id)
    if not prompt_data:
        say(f"Prompt ID {prompt_id} not found in actionable prompts.")
        return

    prompt_text = prompt_data["Prompt"]
    say(f"Running Prompt ID {prompt_id}: {prompt_text}")

    # Run through GPT and get result
    result = execute_prompt_with_gpt(prompt_text, prompt_data.get("Business Function", "General"))

    # Reply with result
    say(f"*Executed Prompt:*\n{prompt_text}\n\n*Result:*\n{result}")

    # Update status in workbook
    update_prompt_status(prompt_id, "Executed")


if __name__ == "__main__":
    print("🚀 Starting Prompt Collector Slack Bot...")
    handler = SocketModeHandler(app, os.getenv("SLACK_APP_TOKEN"))
    handler.start()
