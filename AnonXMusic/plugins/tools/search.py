from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import yt_dlp
import os
import time
import threading
import requests
from youtube_search import YoutubeSearch
from AnonXMusic import app

cookies_file = "assets/cookies.txt"

# Function to convert time to seconds
def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60**i for i, x in enumerate(reversed(stringt.split(":"))))

# Function to delete file after 20 minutes
def delete_file_after_delay(file_path, delay=1200):
    time.sleep(delay)
    if os.path.exists(file_path):
        os.remove(file_path)

# Function to download and send audio
async def download_and_send_audio(client, chat_id, url_suffix, callback_data=None):
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "cookiefile": "cookies_file",  # Use cookies.txt for authentication
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }
        ],
    }
    try:
        link = f"https://youtube.com{url_suffix}"
        results = YoutubeSearch(url_suffix, max_results=1).to_dict()
        title = results[0]["title"][:40]
        duration = results[0]["duration"]
        views = results[0]["views"]
    except Exception as e:
        await client.send_message(chat_id, "**😴 Song not found**")
        print(str(e))
        return

    if callback_data:
        await callback_data.message.edit_text("» Downloading...\n\nPlease wait...")
    else:
        await client.send_message(chat_id, "» Downloading...\n\nPlease wait...")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(link, download=False)
            audio_file = ydl.prepare_filename(info_dict)
            ydl.process_info(info_dict)

        caption = f"**Title:** {title}\n**Duration:** `{duration}`\n**Views:** `{views}`\n**Requested by:** {callback_data.from_user.mention if callback_data else chat_id}"

        duration_sec = time_to_seconds(duration)
        await client.send_audio(
            chat_id,
            audio=open(audio_file, "rb"),
            caption=caption,
            performer="AnonXMusic",
            title=title,
            duration=duration_sec,
        )
    except Exception as e:
        await client.send_message(chat_id, f"**» Downloading error, please report this at » [Support Chat](t.me/SUPPORT_CHAT) 💕**\n\n**Error:** {e}")
        print(e)
        return
    finally:
        try:
            os.remove(audio_file)
        except Exception as e:
            print(e)

# Command handler for /find, /song, and /fsong
@app.on_message(filters.command(["find", "song", "fsong"], prefixes=["/", "!"]))
async def find(client, message):
    chat_id = message.chat.id
    try:
        query = " ".join(message.command[1:])
    except IndexError:
        await client.send_message(chat_id, "Please provide a song name to search.")
        return

    try:
        results = YoutubeSearch(query, max_results=20).to_dict()
        buttons = []
        for i, result in enumerate(results):
            title = result['title'][:40]
            duration = result['duration']
            buttons.append(InlineKeyboardButton(f"{title} - {duration}", callback_data=result['url_suffix']))
        
        # Pagination: Display only 5 buttons per page
        pages = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
        page_data = {"pages": pages, "current_page": 0}
        page_buttons = pages[0] + [InlineKeyboardButton("Next Page", callback_data="next_page_1")]

        reply_markup = InlineKeyboardMarkup(page_buttons)
        await client.send_message(chat_id, "Select a song:", reply_markup=reply_markup)
    except Exception as e:
        await client.send_message(chat_id, "**😴 Song not found on YouTube.**\n\n» Please check the spelling and try again!")
        print(str(e))

# Callback query handler for inline buttons
@app.on_callback_query()
async def handle_callback_query(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    if data.startswith("next_page_"):
        # Handle pagination
        page_number = int(data.split("_")[2])
        results = YoutubeSearch(query, max_results=20).to_dict()
        buttons = []
        for i, result in enumerate(results):
            title = result['title'][:40]
            duration = result['duration']
            buttons.append(InlineKeyboardButton(f"{title} - {duration}", callback_data=result['url_suffix']))
        
        # Pagination: Display only 5 buttons per page
        pages = [buttons[i:i + 5] for i in range(0, len(buttons), 5)]
        page_buttons = pages[page_number] + [InlineKeyboardButton("Next Page", callback_data=f"next_page_{page_number + 1}")]

        reply_markup = InlineKeyboardMarkup(page_buttons)
        await callback_query.message.edit_reply_markup(reply_markup=reply_markup)
    else:
        # Handle song selection
        await download_and_send_audio(client, chat_id, data, callback_query)