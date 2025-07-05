import os
import logging
import asyncio
from telegram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ========== CONFIG ==========

BOT_TOKEN = '8134658376:AAFTmSw2ZxCaTmRGqEyW2Kd1stNSLTrSXB4'
CHAT_ID = 5816675516
MEDIA_PATH = 'media'
TEXTS_FILE = 'texts/texts.txt'
# ============================

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
scheduler = AsyncIOScheduler()

# Track index across all types
media_index = {'value': 0}


def get_sorted_media_files(exts):
    files = [f for f in os.listdir(MEDIA_PATH) if f.lower().endswith(exts)]
    return sorted(files)


def get_texts():
    if not os.path.exists(TEXTS_FILE):
        return []
    with open(TEXTS_FILE, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


async def send_reminder(time_of_day):
    text_list = get_texts()
    image_files = get_sorted_media_files(('.jpg', '.png'))
    audio_files = get_sorted_media_files(('.mp3', '.ogg'))

    total = max(len(text_list), len(image_files), len(audio_files))
    if total == 0:
        await bot.send_message(chat_id=CHAT_ID, text="⚠️ No reminder content found.")
        return

    index = media_index['value'] % total
    await bot.send_message(chat_id=CHAT_ID, text=f"🔔 {time_of_day.capitalize()} Reminder")

    # Send text
    if index < len(text_list):
        await bot.send_message(chat_id=CHAT_ID, text=text_list[index])

    # Send audio
    if index < len(audio_files):
        audio_path = os.path.join(MEDIA_PATH, audio_files[index])
        if os.path.getsize(audio_path) > 0:
            with open(audio_path, 'rb') as audio:
                await bot.send_audio(chat_id=CHAT_ID, audio=audio)

    # Send image
    if index < len(image_files):
        image_path = os.path.join(MEDIA_PATH, image_files[index])
        if os.path.getsize(image_path) > 0:
            with open(image_path, 'rb') as img:
                await bot.send_photo(chat_id=CHAT_ID, photo=img)

    media_index['value'] += 1


# Scheduling with wrapper
def schedule_job(time_of_day, hour, minute):
    def job():
        asyncio.run(send_reminder(time_of_day))
    scheduler.add_job(job, 'cron', hour=hour, minute=minute)



async def main():
    logging.info("Reminder bot started...")
    schedule_job("morning", 7, 0)
    schedule_job("afternoon", 12, 0)
    schedule_job("evening", 20, 0)
    schedule_job("custom", 10, 0)
    scheduler.start()

    # Optional test now
    await send_reminder("test")

    while True:
        await asyncio.sleep(60)


from flask import Flask
import threading

# Create a minimal Flask app just to fake a web server
app = Flask(__name__)


@app.route('/')
def home():
    return "Reminder bot is running!"


def run_web_server():
    app.run(host="0.0.0.0", port=10000)


if __name__ == "__main__":
    # Run the dummy web server in a background thread
    threading.Thread(target=run_web_server).start()

    # Start your Telegram bot normally
    import asyncio

    asyncio.run(main())
