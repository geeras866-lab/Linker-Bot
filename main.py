import os
import threading
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
        "🤖 **Media Downloader Bot is Online!**\n\n"
        "🔗 YouTube link or Direct download link ikkada pampandi. "
        "Nenu daanini download chesi meeku pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Message Handler (YouTube & Direct Link Downloader)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("❌ Dayachesi valid URL pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Downloading file... Kasepu agandi.")
    
    output_filename = "downloaded_video.mp4"
    
    try:
        # Check if it's a YouTube link
        if "youtube.com" in url or "youtu.be" in url:
            ydl_opts = {
                'format': 'best[filesize<50M]/best', # Free tier kosam size limit pettam
                'outtmpl': output_filename,
                'quiet': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        else:
            # Direct link aithe requests dwara save cheyadam
            import requests
            r = requests.get(url, stream=True)
            with open(output_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)

        # Telegram ki video/file pampadam
        await update.message.reply_video(
            video=open(output_filename, 'rb'),
            caption="📁 **Mee video/file successfully deliver aindi!**",
            parse_mode="Markdown"
        )
        
        # File pampaka server lo unna local file ni delete cheseydam (Space save avvadaniki)
        if os.path.exists(output_filename):
            os.remove(output_filename)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n`{str(e)}`\n\n"
            f"*(Note: Video size ekkuva unte Render free tier lo download avvadu)*",
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
