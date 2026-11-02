import os
import threading
import requests
import yt_dlp
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
        "🤖 **Downloader Bot is Ready!**\n\n"
        "🔗 YouTube link or Direct download link ikkada pampandi. "
        "Nenu daanini download chesi file/video laaga pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("❌ Dayachesi valid URL pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Downloading file... Kasepu agandi.")
    
    output_filename = "downloaded_file.mp4"
    
    try:
        # 1. YouTube link aithe yt-dlp tho download cheyadam
        if "youtube.com" in url or "youtu.be" in url:
            ydl_opts = {
                'format': 'best[filesize<50M]/best',
                'outtmpl': output_filename,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        
        # 2. Normal direct link aithe requests tho download cheyadam
        else:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            response = requests.get(url, headers=headers, stream=True)
            
            if response.status_code == 200:
                with open(output_filename, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                raise Exception(f"Server responded with status code: {response.status_code}")

        # File successfully download ayyaka Telegram ki document/video laaga pampadam
        await update.message.reply_document(
            document=open(output_filename, 'rb'),
            caption="📁 **Mee file successfully deliver aindi!**",
            parse_mode="Markdown"
        )
        
        # Server space clean cheyadaniki file delete cheseydam
        if os.path.exists(output_filename):
            os.remove(output_filename)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n`{str(e)}`",
            parse_mode="Markdown"
        )
        # Error ochina file unte remove cheyali
        if os.path.exists(output_filename):
            os.remove(output_filename)

def main():
    if not BOT_TOKEN:
        print("Error: BOT_TOKEN environment variable is missing!")
        return

    # Flask server ni background lo run chedam
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    # Telegram Bot setup
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("Bot is up and running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
