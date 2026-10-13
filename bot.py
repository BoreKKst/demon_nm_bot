import os
import asyncio
import threading
from flask import Flask
import discord
from discord.ext import tasks
import yt_dlp

# --- Flask Web Server для keep-alive (24/7) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive and running 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

# Запускаем Flask в отдельном потоке
threading.Thread(target=run_flask).start()

# --- Discord Bot Setup ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "demon_nm")
CHECK_MINUTES = int(os.getenv("CHECK_MINUTES", "5"))

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

was_live = False

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    if not check_tiktok_live.is_running():
        check_tiktok_live.start()

@tasks.loop(minutes=CHECK_MINUTES)
async def check_tiktok_live():
    global was_live
    channel = client.get_channel(DISCORD_CHANNEL_ID)
    if not channel:
        print(f"Error: Discord channel {DISCORD_CHANNEL_ID} not found.")
        return

    url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live"
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            is_live = info.get('is_live', False)

            if is_live and not was_live:
                was_live = True
                stream_title = info.get('title', 'Трансляция началась!')
                stream_url = info.get('webpage_url', url)
                thumbnail_url = info.get('thumbnail', '')

                # Создаем Embed карточку
                embed = discord.Embed(
                    title=stream_title,
                    description="иди скорее 🚀",
                    color=discord.Color.from_rgb(255, 0, 80),
                    url=stream_url
                )

                if thumbnail_url:
                    embed.set_image(url=thumbnail_url)

                await channel.send(
                    content=f"@everyone 🔴 **{TIKTOK_USERNAME} в эфире!**", 
                    embed=embed
                )
            elif not is_live:
                was_live = False

    except Exception as e:
        # Ошибка означает, что стрима нет или временная задержка
        print(f"TikTok check status: {e}")

client.run(DISCORD_TOKEN)
