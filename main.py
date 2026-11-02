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

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Video Downloader Bot is Online!**\n\n"
        "🔗 HubCDN, YouTube, or Direct video links ikkada pampandi. "
        "Nenu daanini fast ga download chesi **direct video file** laaga ikkade pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Video Downloader using yt-dlp
def download_video(url, output_filename="downloaded_video.mp4"):
    ydl_opts = {
        'format': 'best[filesize<400M]/best',  # Render free tier RAM limit kosam size control
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    return output_filename

# Link Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "magnet:?" in text.lower():
        await update.message.reply_text("⚠️ **Note:** Render free server lo Magnet links support avvavu. Dayachesi HubCDN or Direct video links pampandi!")
        return
        
    if not "http" in text.lower():
        await update.message.reply_text("❌ Dayachesi valid video link pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Video download avtundi... Kasepu agandi.")
    
    filename = "downloaded_video.mp4"
    
    try:
        # Download video using yt-dlp
        download_video(text, filename)
        
        if not os.path.exists(filename):
            raise Exception("File download avvaledu. Link work avtaledu.")
            
        # Telegram ki direct video file laaga pampadam (with streaming support)
        await update.message.reply_video(
            video=open(filename, 'rb'),
            caption="🎬 **Mee video successfully deliver aindi!**",
            parse_mode="Markdown",
            supports_streaming=True
        )
        
        # Server space clean cheyadaniki file delete cheseydam
        if os.path.exists(filename):
            os.remove(filename)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n`{str(e)}`\n\n*(Note: File size ekkuva unna leda link expire aina download avvadu)*",
            parse_mode="Markdown"
        )
        if os.path.exists(filename):
            os.remove(filename)

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
