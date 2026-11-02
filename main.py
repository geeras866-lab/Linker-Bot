import os
import time
import asyncio
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
        "🔗 HubCDN or Direct video links ikkada pampandi. "
        "Nenu live download progress (% speed) tho saha chupinchi **direct video file** pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# Link Handler with Live Progress
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "magnet:?" in text.lower():
        await update.message.reply_text("⚠️ **Note:** Render free server lo Magnet links support avvavu. HubCDN or Direct video links pampandi!")
        return
        
    if not "http" in text.lower():
        await update.message.reply_text("❌ Dayachesi valid video link pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Download start avtundi... 0%")
    filename = "downloaded_video.mp4"
    
    last_update_time = [0]

    # Progress Hook function (Downloading percentage live lo update chestundi)
    def progress_hook(d):
        if d['status'] == 'downloading':
            current_time = time.time()
            # Telegram flood limit avoid cheyadaniki every 3 seconds ki okasari update chestam
            if current_time - last_update_time[0] > 3:
                last_update_time[0] = current_time
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                try:
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(
                            f"📥 **Downloading Progress:**\n\n"
                            f"📊 **Progress:** `{percent}`\n"
                            f"⚡ **Speed:** `{speed}`\n"
                            f"⏱️ **ETA:** `{eta}`",
                            parse_mode="Markdown"
                        ),
                        context.application.bot.loop
                    )
                except Exception:
                    pass

    ydl_opts = {
        'format': 'best[filesize<400M]/best',
        'outtmpl': filename,
        'quiet': True,
        'no_warnings': True,
        'progress_hooks': [progress_hook],
    }
    
    try:
        # Background lo yt-dlp download run avvadaniki executor vadatam
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).download([text]))
        
        if not os.path.exists(filename):
            raise Exception("File download avvaledu. Link work avtaledu.")
            
        await status_msg.edit_text("📤 **Video upload avtundi, kasepu agandi...**", parse_mode="Markdown")
            
        # Telegram ki direct video file laaga pampadam
        await update.message.reply_video(
            video=open(filename, 'rb'),
            caption="🎬 **Mee video successfully deliver aindi!**",
            parse_mode="Markdown",
            supports_streaming=True
        )
        
        # Server clean cheyadam
        if os.path.exists(filename):
            os.remove(filename)
            
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n`{str(e)}`",
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

    print("Progress bot is up and running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
