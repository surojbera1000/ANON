import time
import re
import random
import asyncio

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from pyrogram.errors.exceptions.not_acceptable_406 import ChannelPrivate
from pyrogram.errors.exceptions.flood_420 import SlowmodeWait
from ytSearch import VideosSearch

import config
from AnonXMusic import app
from AnonXMusic.misc import _boot_
from AnonXMusic.plugins.sudo.sudoers import sudoers_list
from AnonXMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
    blacklist_chat,
)
from AnonXMusic.utils.decorators.language import LanguageStart
from AnonXMusic.utils.formatters import get_readable_time
from AnonXMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS, LOGGER_ID
from strings import get_string

# আপনার দেওয়া ভিডিও লিংক
START_VIDEO_URLS = [
    "https://files.catbox.moe/3kb787.mp4",
    "https://files.catbox.moe/aoafwn.mp4",
    "https://files.catbox.moe/vlcqn3.mp4",
    "https://files.catbox.moe/93r50w.mp4",
    "https://files.catbox.moe/f544nb.mp4",
    "https://files.catbox.moe/93r50w.mp4",
    "https://files.catbox.moe/vlcqn3.mp4",
]

# ফ্লাইং লাভের জন্য অ্যানিমেটেড স্টিকার (উড়ন্ত হৃদয়)
FLYING_LOVE_STICKERS = [
    "CAACAgUAAxkBAAPnXUJkAAH8mXkAARUAAWnIAAV_AAFGAAEWCQACOQsAAgIYVhVbUpEWeWRUUDME",  # Flying heart sticker 1
    "CAACAgUAAxkBAAPoXUJkAAH8mXoAARUAAWnIAAV_AAFGAAEWCQACOgsAAgIYVhVbUpEWeWRUUDME",  # Flying heart sticker 2
]

# ফ্লাইং লাভ ইফেক্ট (একাধিক অ্যানিমেটেড স্টিকার + রিঅ্যাকশন)
async def send_flying_love_effect(message: Message):
    """ভিডিওর উপরে ফ্লাইং লাভ ইফেক্ট তৈরি করবে"""
    try:
        # 1. প্রথমে দ্রুত রিঅ্যাকশন দেবে (Telegram এর ডিফল্ট)
        for _ in range(5):
            await message.react('❤️')
            await asyncio.sleep(0.15)
        
        # 2. অ্যানিমেটেড ফ্লাইং লাভ স্টিকার পাঠাবে (উড়ন্ত ইফেক্ট)
        for i in range(8):  # 8 বার উড়ন্ত স্টিকার
            sticker = random.choice(FLYING_LOVE_STICKERS)
            await message.reply_sticker(sticker)
            await asyncio.sleep(0.2)
            
        # 3. আবারও রিঅ্যাকশন (ফ্লাইং ফিল দিতে)
        for _ in range(3):
            await message.react('❤️')
            await asyncio.sleep(0.1)
            
    except Exception as e:
        print(f"Flying love effect error: {e}")

# ভিডিও সেন্ড করার ফাংশন
async def send_start_video(client, message: Message, caption_text: str, reply_markup=None):
    """ভিডিও + ফ্লাইং লাভ ইফেক্ট"""
    try:
        video_url = random.choice(START_VIDEO_URLS)
        
        video_msg = await message.reply_video(
            video=video_url,
            caption=caption_text,
            reply_markup=reply_markup,
            supports_streaming=True
        )
        
        # ফ্লাইং লাভ ইফেক্ট শুরু
        await send_flying_love_effect(video_msg)
        
        return video_msg
    except Exception as e:
        print(f"Video send error: {e}")
        return await message.reply_text("❌ ভিডিও লোড করতে সমস্যা হচ্ছে")


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            await send_start_video(
                client, message,
                caption_text=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard
            )
            return
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT),
                    ],
                ]
            )
            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
    else:
        out = private_panel(_)
        await send_start_video(
            client, message,
            caption_text=_["start_2"].format(message.from_user.mention, app.mention),
            reply_markup=InlineKeyboardMarkup(out)
        )
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    try:
        await send_start_video(
            client, message,
            caption_text=_["start_1"].format(app.mention, get_readable_time(uptime)),
            reply_markup=InlineKeyboardMarkup(out)
        )
        return await add_served_chat(message.chat.id)
    except ChannelPrivate:
        return
    except SlowmodeWait as e:
        asyncio.sleep(e.value)
        try:
            await send_start_video(
                client, message,
                caption_text=_["start_1"].format(app.mention, get_readable_time(uptime)),
                reply_markup=InlineKeyboardMarkup(out)
            )
            return await add_served_chat(message.chat.id)
        except:
            return


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)
                
                ch = await app.get_chat(message.chat.id)
                if (ch.title and re.search(r'[\u1000-\u109F]', ch.title)) or \
                    (ch.description and re.search(r'[\u1000-\u109F]', ch.description)):
                        await blacklist_chat(message.chat.id)
                        await message.reply_text("This group is not allowed to play songs")
                        await app.send_message(LOGGER_ID, f"This group has been blacklisted automatically due to myanmar characters in the chat title, description or message \n Title:{ch.title} \n ID:{message.chat.id}")
                        return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                await send_start_video(
                    client, message,
                    caption_text=_["start_3"].format(
                        message.from_user.first_name,
                        app.mention,
                        message.chat.title,
                        app.mention,
                    ),
                    reply_markup=InlineKeyboardMarkup(out)
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)