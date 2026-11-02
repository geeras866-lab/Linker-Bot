import os
import time
import threading
import yt_dlp
import libtorrent as lt
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Render sleep avvakunda undataniki Flask web server
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "Universal Video Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 **Universal Video Bot Ready!**\n\n"
        "🔗 **Magnet Link** aina, **HubCDN / Direct Video Links** aina ikkada pampandi. "
        "Nenu daanini download chesi **direct video file** laaga ikkade pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# 1. Torrent / Magnet Downloader
def download_torrent(magnet_link, save_path="downloads"):
    if not os.path.exists(save_path):
        os.makedirs(save_path)
        
    ses = lt.session()
    ses.listen_port(6881, 6891)
    
    params = {
        'save_path': save_path,
        'storage_mode': lt.storage_mode_t(2)
    }
    
    handle = lt.add_magnet_uri(ses, magnet_link, params)
    
    while not handle.has_metadata():
        time.sleep(1)
        
    while not handle.is_seed():
        time.sleep(3)
        
    files = []
    item = handle.get_torrent_info()
    for i in range(item.num_files()):
        files.append(os.path.join(save_path, item.files().file_path(i)))
        
    return files

# 2. HubCDN / Direct / yt-dlp Supported Link Downloader
def download_web_video(url, output_filename="downloaded_video.mp4"):
    ydl_opts = {
        'format': 'best[filesize<500M]/best',
        'outtmpl': output_filename,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])
        
    return output_filename

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Check if text contains magnet or http anywhere (Telegram formatting bypass kosam)
    is_magnet = "magnet:?" in text.lower() or "xt=urn:btih:" in text.lower()
    is_http = "http" in text.lower()
    
    if not is_magnet and not is_http:
        await update.message.reply_text("❌ Dayachesi valid Link (HTTP / Magnet) pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Link process avtundi... Kasepu agandi (Downloading started).")
    
    downloaded_files = []
    
    try:
        # A) Magnet Link aithe
        if is_magnet:
            # Clean text to ensure correct magnet URI extraction
            if "magnet:?" in text:
                magnet_uri = text[text.find("magnet:?"):].strip()
            else:
                magnet_uri = text
            downloaded_files = download_torrent(magnet_uri)
            
        # B) HubCDN, Direct, or yt-dlp supported links aithe
        else:
            filename = download_web_video(text)
            if os.path.exists(filename):
                downloaded_files.append(filename)
                
        if not downloaded_files:
            raise Exception("File download avvaledu. Link work avtaledu.")
            
        # Files anni Telegram ki direct video laaga pampadam
        for file_path in downloaded_files:
            if os.path.exists(file_path):
                await update.message.reply_video(
                    video=open(file_path, 'rb'),
                    caption=f"🎬 **Mee Video Ready:** `{os.path.basename(file_path)}`",
                    parse_mode="Markdown",
                    supports_streaming=True
                )
                
                try:
                    os.remove(file_path)
                except:
                    pass
        
        await status_msg.delete()
        
    except Exception as e:
        await status_msg.edit_text(
            f"❌ **Error vachindi:**\n`{str(e)}`",
            parse_mode="Markdown"
        )

def main():
    if not BOT_TOKEN:
        return

    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    application.run_polling()

if __name__ == "__main__":
    main()
