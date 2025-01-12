import datetime
import json
import logging
import os
import urllib
from pathlib import Path
from urllib.parse import urlparse

from pydub import AudioSegment
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

from audio import match_target_amplitude
from youtube import get_shows, get_episode

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

ADMIN_USERS = os.getenv('ADMIN_USERS').split(",")
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
DOWNLOAD_URL = os.getenv('DOWNLOAD_URL')


async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id in ADMIN_USERS:
        await update.message.reply_text(f'You have not been whitelisted')
    else:
        try:
            info_dict = get_shows()

            if "entries" not in info_dict:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, text="No episodes found")

            episodes = info_dict["entries"]
            episodes.reverse()
            context.user_data['episodes'] = episodes
            logger.info(f"Found episodes {', '.join([episode['title'] for episode in episodes])}")

            for episode in episodes:
                keyboard = [
                    [InlineKeyboardButton("Download",
                                          callback_data=episode['id']), ]
                ]
                keyboard_markup = InlineKeyboardMarkup(keyboard)

                await context.bot.send_photo(
                    chat_id=update.effective_chat.id, photo=episode["thumbnails"][-1]['url'],
                    caption=f"{episode['title']}",
                    reply_markup=keyboard_markup)
        except Exception as e:
            logger.error(f"Failed to get or process episodes: {e}")
            await update.message.reply_text("Failed to get episodes")


async def keyboard_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # Use cached video question was clicked, query data is yes or no, video information should be in context.user_data['episode']
    if query.data in ["yes", "no"]:
        if query.data == "yes":
            try:
                pass
            except Exception as e:
                logger.error(f"Could not access episode stored in user data: {e}")
            episode = context.user_data["episode"]
            logger.info(f"Using cached episode {episode['title']}")
            await query.answer()
            await context.bot.send_message(
                chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                text=f"Using cached file, get it from {DOWNLOAD_URL}/{query.data}.mp3")
    # Download for some video was clicked, query data is the video id
    else:
        possible_user_data_episode = next(
            episode for episode in context.user_data['episodes'] if episode['id'] == query.data)
        context.user_data['episode'] = possible_user_data_episode if possible_user_data_episode else None

        possible_cached_file = Path(f"./output/{query.data}.mp3")

        if possible_user_data_episode and possible_cached_file.exists():
            keyboard = [
                [InlineKeyboardButton("Yes",
                                      callback_data="yes"),
                 InlineKeyboardButton("No",
                                      callback_data="no")]
            ]
            keyboard_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                text=f"Found a cached video from {datetime.datetime.fromtimestamp(possible_cached_file.stat().st_birthtime).strftime('%d.%m.%Y %H:%M')} do you want to use it?",
                reply_markup=keyboard_markup)
            await query.answer()
        else:
            # Remove dangling cached file
            if possible_cached_file.exists():
                possible_cached_file.unlink()

            episode = next(episode for episode in context.user_data['episodes'] if episode['id'] == query.data)
            if episode:
                logger.info(f"Downloading episode {episode['title']}, this will take a few minutes. Sit tight!")
            else:
                logger.warning("Did not find episode information in user data")
                logger.info(f"Downloading episode https://www.youtube.com/watch?v={query.data}")
            await context.bot.send_message(
                chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                text="Downloading this episode")
            await query.answer()
            try:
                get_episode(f"https://www.youtube.com/watch?v={query.data}")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                    text="Normalizing audio, this will also take a bit...")
                match_target_amplitude(f"{query.data}.mp3")
                await context.bot.send_message(
                    chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                    text=f"Download completed, get the file from {DOWNLOAD_URL}/{query.data}.mp3")
            except Exception as e:
                logger.error(f"yt-dlp failed to download the video: {e}")
                context.bot.send_message(
                    chat_id=update.effective_chat.id, reply_to_message_id=query.message.message_id,
                    text="yt-dlp failed to download the video")


if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", handle_start))
    app.add_handler(CallbackQueryHandler(keyboard_button_handler))

    app.run_polling()
