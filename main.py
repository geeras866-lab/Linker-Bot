import os
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Render sleep avvakunda undataniki Flask web server
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

# Bot Token from Environment Variables
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 **Welcome to Link-to-File Bot!**\n\n"
        "🔗 Mee direct download link ikkada pampandi. "
        "Nenu daanini file/video laaga convert chesi ikkade isthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Link handler (File download & send logic)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("❌ Dayachesi valid URL pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Processing link... Kasepu agandi.")
    
    try:
        # Telegram servers direct ga URL nunchi file ni download chesi pampistayi
        # (Idi direct download links like .mp4, .mkv, .zip lanti vatiki baga pani chestundi)
        await update.message.reply_document(
            document=url, 
            caption="📁 **Mee file successfully deliver aindi!**",
            parse_mode="Markdown"
        )
        
        # Success ayyaka status message ni theesestham
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n{str(e)}\n\n"
            f"*(Note: Link kachithamga direct file download link ayi undali)*"
        )

def main():
    # Flask server ni background lo run chedam
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram Bot setup
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Simple Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
