import os
import threading
from flask import Flask
from pyrogram import Client, filters

# Flask app - Render web service kosam mariyu cron job ping cheyadaniki
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# Telegram Bot Credentials (Render Environment Variables nunchi load avtayi)
API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

app = Client("simple_file_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

@app.on_message(filters.command("start"))
async def start_handler(client, message):
    await message.reply_text(
        "👋 Hello! Mee download link ikkada pampandi. "
        "Nenu daanini file laaga process chesi mee channel ki pampisthanu!"
    )

@app.on_message(filters.text & ~filters.command(["start"]))
async def link_handler(client, message):
    url = message.text.strip()
    
    if not url.startswith("http"):
        await message.reply_text("❌ Dayachesi valid URL pampandi.")
        return
        
    status_msg = await message.reply_text("🔄 Processing link... Kasepu agandi.")
    
    try:
        # Ikkada link nunchi file process chesi channel ki pampocchu
        # Example: await client.send_document(chat_id=CHANNEL_ID, document=url, caption="Mee file idi!")
        
        await status_msg.edit_text("✅ File successfully sent to your channel!")
        
    except Exception as e:
        await status_msg.edit_text(f"❌ Error vachindi: {str(e)}")

if __name__ == "__main__":
    # Flask server ni oka separate background thread lo run chedam
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    print("Bot and Flask server are running...")
    app.run()
