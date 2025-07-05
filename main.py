import os
import json
import logging
import asyncio
from datetime import datetime
from telegram import Bot
from apscheduler.schedulers.blocking import BlockingScheduler
from flask import Flask
import threading

# === CONFIG ===
BOT_TOKEN = os.getenv("8134658376:AAFTmSw2ZxCaTmRGqEyW2Kd1stNSLTrSXB4")
CHAT_ID = int(os.getenv("5816675516"))
MEDIA_DIR = "media"
SCHEDULE_FILE = "schedule.json"
INDEX_FILE = "schedule_index.json"
TIMEZONE_OFFSET = 5  # Adjust to your time zone
# ===============

bot = Bot(token=BOT_TOKEN)
scheduler = BlockingScheduler()
logging.basicConfig(level=logging.INFO)

# === UTILITIES ===

def load_schedule():
    with open(SCHEDULE_FILE, 'r') as f:
        return json.load(f)

def load_index():
    if os.path.exists(INDEX_FILE):
        with open(INDEX_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_index(index):
    with open(INDEX_FILE, 'w') as f:
        json.dump(index, f)

async def send_file(filename):
    path = os.path.join(MEDIA_DIR, filename)
    if not os.path.exists(path) or os.stat(path).st_size == 0:
        logging.warning(f"⚠️ Skipped missing or empty file: {filename}")
        return

    try:
        if filename.endswith('.jpg') or filename.endswith('.png'):
            with open(path, 'rb') as img:
                await bot.send_photo(chat_id=CHAT_ID, photo=img)

        elif filename.endswith('.mp3') or filename.endswith('.ogg'):
            with open(path, 'rb') as audio:
                await bot.send_audio(chat_id=CHAT_ID, audio=audio)

        elif filename.endswith('.mp4'):
            with open(path, 'rb') as vid:
                await bot.send_video(chat_id=CHAT_ID, video=vid)

        elif filename.endswith('.txt'):
            with open(path, 'r', encoding='utf-8') as txt:
                await bot.send_message(chat_id=CHAT_ID, text=txt.read())

        else:
            logging.warning(f"Unsupported file type: {filename}")
    except Exception as e:
        logging.error(f"❌ Failed to send {filename}: {e}")

def schedule_jobs():
    schedule = load_schedule()
    index = load_index()

    for time_str, file_list in schedule.items():
        try:
            hour, minute = map(int, time_str.split(":"))
            hour_utc = (hour - TIMEZONE_OFFSET) % 24

            def make_job(time_str=time_str):
                def job():
                    try:
                        schedule = load_schedule()
                        index = load_index()
                        files = schedule.get(time_str, [])
                        if not files:
                            return
                        idx = index.get(time_str, 0) % len(files)
                        filename = files[idx]
                        asyncio.run(send_file(filename))
                        index[time_str] = idx + 1
                        save_index(index)
                    except Exception as e:
                        logging.error(f"Job error for {time_str}: {e}")
                return job

            scheduler.add_job(make_job(), 'cron', hour=hour_utc, minute=minute)
            logging.info(f"✅ Scheduled {time_str} → {file_list}")

        except Exception as e:
            logging.error(f"Error scheduling {time_str}: {e}")

# === FLASK DUMMY WEB SERVER ===
app = Flask(__name__)
@app.route('/')
def home():
    return "Reminder bot is running!"

def run_web():
    app.run(host="0.0.0.0", port=10000)

# === MAIN ENTRY ===
if __name__ == "__main__":
    threading.Thread(target=run_web).start()
    schedule_jobs()
    scheduler.start()

