import os
import time
import asyncio
import threading
import requests
from bs4 import BeautifulSoup
import yt_dlp
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# Render sleep avvakunda undataniki Flask web server
app_flask = Flask(__name__)

@app_flask.route("/")
def home():
    return "JJ Movies Bot is active and running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app_flask.run(host="0.0.0.0", port=port)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🎬 **JJ Movies Official Bot**\n\n"
        "🔗 HubCDN or Direct video links ikkada pampandi. "
        "Nenu clean file name (**JJ Movies**) mariyu live progress tho video pampisthanu!"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# HubCDN page nunchi original video link ni extract chese function
def extract_hubcdn_video_url(hubcdn_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(hubcdn_url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            video_tag = soup.find('video')
            if video_tag:
                source_tag = video_tag.find('source')
                if source_tag and source_tag.get('src'):
                    return source_tag['src']
                if video_tag.get('src'):
                    return video_tag['src']
            
            for script in soup.find_all('script'):
                script_text = script.text
                if '.mp4' in script_text:
                    import re
                    match = re.search(r'https?://[^\s<>"]+?\.mp4[^\s<>"]*', script_text)
                    if match:
                        return match.group(0)
                        
    except Exception as e:
        print(f"Extraction error: {e}")
        
    return hubcdn_url

# File name ni clean chesi JJ Movies add chese function
def clean_and_rename_file(file_path):
    directory, original_filename = os.path.split(file_path)
    
    # Unwanted watermark/branding words remove cheyadam
    cleaned_name = original_filename
    unwanted_words = ["www.5MovieRulz.company - ", "5MovieRulz", "www.Movierulz.pe - ", "www.Movierulz.com - "]
    for word in unwanted_words:
        cleaned_name = cleaned_name.replace(word, "")
        
    base_name, ext = os.path.splitext(cleaned_name)
    
    # Cleaned final name with JJ Movies tag
    new_filename = f"Aadarsha Kutumbam - [JJ Movies]{ext}" if "Aadarsha" in base_name else f"{base_name} - [JJ Movies]{ext}"
    new_file_path = os.path.join(directory, new_filename)
    
    if os.path.exists(file_path):
        if os.path.exists(new_file_path):
            os.remove(new_file_path)
        os.rename(file_path, new_file_path)
        
    return new_file_path

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if "magnet:?" in text.lower():
        await update.message.reply_text("⚠️ Render free server lo magnet links support avvavu. HubCDN or Direct links pampandi!")
        return
        
    if not "http" in text.lower():
        await update.message.reply_text("❌ Dayachesi valid video link pampandi.")
        return
        
    status_msg = await update.message.reply_text("🔄 Link parse avtundi... Kasepu agandi.")
    filename = "downloaded_video.mp4"
    last_update_time = [0]

    actual_video_url = extract_hubcdn_video_url(text)

    def progress_hook(d):
        if d['status'] == 'downloading':
            current_time = time.time()
            if current_time - last_update_time[0] > 2:
                last_update_time[0] = current_time
                percent = d.get('_percent_str', '0%').strip()
                speed = d.get('_speed_str', 'N/A').strip()
                eta = d.get('_eta_str', 'N/A').strip()
                
                try:
                    p_val = float(percent.replace('%', ''))
                    filled = int(p_val // 10)
                    bar = "■" * filled + "□" * (10 - filled)
                except:
                    bar = "----------"
                
                try:
                    asyncio.run_coroutine_threadsafe(
                        status_msg.edit_text(
                            f"📥 **JJ MOVIES DOWNLOADING...**\n\n"
                            f"[{bar}] `{percent}`\n"
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
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        },
    }
    
    try:
        loop = asyncio.get_running_loop()
        
        def download_yt():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([actual_video_url])

        try:
            await loop.run_in_executor(None, download_yt)
        except Exception as yt_err:
            headers = ydl_opts['http_headers']
            r = requests.get(actual_video_url, headers=headers, stream=True)
            if r.status_code == 200:
                with open(filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
            else:
                raise yt_err

        if not os.path.exists(filename) or os.path.getsize(filename) < 100000:
            raise Exception("Real video file download avvaledu. Link expire aindi.")
            
        # Clean file name and add JJ Movies tag
        final_file_path = clean_and_rename_file(filename)
        final_filename_only = os.path.basename(final_file_path)
            
        await status_msg.edit_text(
            "📤 **UPLOADING TO JJ MOVIES...**\n\n"
            "[■■■■■■■■■■] `100%`\n"
            "🚀 *Sending video file to channel...*",
            parse_mode="Markdown"
        )
        
        caption_text = (
            f"🎬 **JJ Movies Official**\n\n"
            f"📁 **File Name:** `{final_filename_only}`\n"
            f"✨ *Successfully Downloaded & Uploaded!*"
        )

        await update.message.reply_video(
            video=open(final_file_path, 'rb'),
            caption=caption_text,
            parse_mode="Markdown",
            supports_streaming=True
        )
        
        if os.path.exists(final_file_path):
            os.remove(final_file_path)
            
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
        print("Error: BOT_TOKEN is missing!")
        return

    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("JJ Movies Branded Bot is running successfully...")
    application.run_polling()

if __name__ == "__main__":
    main()
