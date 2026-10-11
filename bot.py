import os
import json
import asyncio
import discord
from discord.ext import tasks, commands
from dotenv import load_dotenv
import yt_dlp

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", "0"))
TIKTOK_USERNAME = os.getenv("TIKTOK_USERNAME", "demon_nm")
CHECK_MINUTES = int(os.getenv("CHECK_MINUTES", "2"))

STATE_FILE = "data/state.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state_data):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state_data, f, ensure_ascii=False, indent=4)

@bot.event
async def on_ready():
    print(f"Бот успешно авторизован как {bot.user} (ID: {bot.user.id})")
    print(f"Мониторинг TikTok @{TIKTOK_USERNAME} (видео + эфиры) каждые {CHECK_MINUTES} мин.")
    if not check_tiktok.is_running():
        check_tiktok.start()

@tasks.loop(minutes=CHECK_MINUTES)
async def check_tiktok():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print(f"[ОШИБКА] Discord-канал с ID {CHANNEL_ID} не найден!")
        return

    loop = asyncio.get_running_loop()
    state = load_state()
    
    # 1. Проверка новых видео
    profile_url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}"
    ydl_opts = {
        'extract_flat': True,
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        def extract_profile():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(profile_url, download=False)
        
        info = await loop.run_in_executor(None, extract_profile)
        if info and 'entries' in info and info['entries']:
            latest_video = info['entries'][0]
            video_id = latest_video.get('id') or latest_video.get('url')
            video_url = latest_video.get('url') or f"https://www.tiktok.com/@{TIKTOK_USERNAME}/video/{video_id}"
            video_title = latest_video.get('title') or latest_video.get('description') or "Новая публикация в TikTok!"
            thumbnail_url = latest_video.get('thumbnail')

            last_id = state.get("last_id")
            if last_id is None:
                state["last_id"] = video_id
                save_state(state)
                print(f"[ИНИЦИАЛИЗАЦИЯ] Запомнено последнее видео: {video_id}")
            elif video_id != last_id:
                state["last_id"] = video_id
                save_state(state)

                embed = discord.Embed(
                    title="🎬 Новое видео в TikTok!",
                    description=video_title[:4000],
                    color=0x00E5FF
                )
                embed.set_author(
                    name=f"@{TIKTOK_USERNAME}",
                    icon_url="https://sf16-scmcdn-va.ibytedtos.com/obj/eden-va2/tteq_zvh_loj/ljhwZthlaukjlkulzlp/tiktok-icon-2.png"
                )
                if thumbnail_url:
                    embed.set_image(url=thumbnail_url)
                embed.url = video_url
                embed.set_footer(text="demon_nm_bot")

                await channel.send(embed=embed)
                print(f"[УСПЕХ] Уведомление о новом видео отправлено!")
    except Exception as e:
        print(f"[Ошибка видео]: {e}")

    # 2. Проверка прямых эфиров (Live)
    live_url = f"https://www.tiktok.com/@{TIKTOK_USERNAME}/live"
    live_ydl_opts = {
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
    }
    try:
        def extract_live():
            with yt_dlp.YoutubeDL(live_ydl_opts) as ydl:
                return ydl.extract_info(live_url, download=False)
        
        live_info = await loop.run_in_executor(None, extract_live)
        is_currently_live = False
        live_title = "Прямой эфир в TikTok!"
        
        if live_info and (live_info.get('is_live') or live_info.get('_type') == 'url'):
            is_currently_live = True
            if live_info.get('title'):
                live_title = live_info.get('title')

        was_live = state.get("is_live", False)

        if is_currently_live and not was_live:
            state["is_live"] = True
            save_state(state)

            embed = discord.Embed(
                title="🔴 ПРЯМОЙ ЭФИР НАЧАЛСЯ!",
                description=f"**{TIKTOK_USERNAME}** запустил стрим в TikTok!\n\n{live_title}",
                color=0xFF0055
            )
            embed.set_author(
                name=f"@{TIKTOK_USERNAME}",
                icon_url="https://sf16-scmcdn-va.ibytedtos.com/obj/eden-va2/tteq_zvh_loj/ljhwZthlaukjlkulzlp/tiktok-icon-2.png"
            )
            embed.url = live_url
            embed.set_footer(text="demon_nm_bot")

            await channel.send(embed=embed)
            print(f"[УСПЕХ] Уведомление об эфире отправлено!")
        elif not is_currently_live and was_live:
            state["is_live"] = False
            save_state(state)
            print(f"[ЛОГ] Эфир завершился.")

    except Exception as e:
        if state.get("is_live", False):
            state["is_live"] = False
            save_state(state)

@check_tiktok.before_loop
async def before_check_timer():
    await bot.wait_until_ready()


from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Bot is active 24/7!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

if __name__ == "__main__":
    keep_alive()
    if not TOKEN:
        print("[ОШИБКА] DISCORD_TOKEN не указан!")
    else:
        bot.run(TOKEN)
