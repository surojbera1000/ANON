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

# আপনার দেওয়া ভিডিও লিংক (7 টা)
START_VIDEO_URLS = [
    "https://files.catbox.moe/3kb787.mp4",
    "https://files.catbox.moe/aoafwn.mp4",
    "https://files.catbox.moe/vlcqn3.mp4",
    "https://files.catbox.moe/93r50w.mp4",
    "https://files.catbox.moe/f544nb.mp4",
    "https://files.catbox.moe/93r50w.mp4",
    "https://files.catbox.moe/vlcqn3.mp4",
]

# হিউজ ফ্লাইং রিঅ্যাকশন (ESHANI স্টাইলে)
async def send_flying_reactions(message: Message):
    """একসাথে অনেকগুলো রিঅ্যাকশন উড়িয়ে দেয় - ESHANI স্টাইল"""
    reactions = ['❤️', '🔥', '🎉', '🥳', '🎸', '💚', '👍', '😍', '🤣', '🎵', '💥', '✨', '🌟', '⭐', '🎶']
    
    # 10-15টা রিঅ্যাকশন এলোমেলোভাবে
    num_reactions = random.randint(10, 15)
    selected_reactions = random.sample(reactions, min(num_reactions, len(reactions)))
    
    for emoji in selected_reactions:
        try:
            await message.react(emoji)
            await asyncio.sleep(0.1)  # স্পিডি রিঅ্যাকশন - ফ্লাইং ইফেক্ট
        except Exception as e:
            print(f"Reaction error: {e}")
            continue

# শুধু ভিডিও সেন্ড করার ফাংশন (ESHANI স্টাইলে)
async def send_start_video(client, message: Message, caption_text: str, reply_markup=None):
    """ESHANI MUSIC স্টাইলে ভিডিও + ফ্লাইং রিঅ্যাকশন"""
    try:
        # র্যান্ডম ভিডিও সিলেক্ট
        video_url = random.choice(START_VIDEO_URLS)
        
        # ক্যাপশন স্টাইল ESHANI এর মতো করে
        styled_caption = f"**✨ {caption_text} ✨**" if not caption_text.startswith("**") else caption_text
        
        # ভিডিও পাঠানো
        video_msg = await message.reply_video(
            video=video_url,
            caption=styled_caption,
            reply_markup=reply_markup,
            supports_streaming=True
        )
        
        # হিউজ ফ্লাইং রিঅ্যাকশন
        await send_flying_reactions(video_msg)
        
        return video_msg
    except Exception as e:
        print(f"Video send error: {e}")
        # ব্যাকআপ: ভিডিও না থাকলে টেক্সট মেসেজ
        return await message.reply_text(f"🌟 {caption_text} 🌟", reply_markup=reply_markup)


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
        # ESHANI স্টাইলে কাস্টম ক্যাপশন
        caption_text = f"**🎵 Hey {message.from_user.mention}!**\n\n**✨ THIS IS «{app.mention}» ✨**\n\n🔗 **A PREMIUM MUSIC PLAYER BOT FOR TELEGRAM GROUP & CHANNEL**\n\n❤️ **POWERED BY KAIZEN**"
        
        await send_start_video(
            client, message,
            caption_text=caption_text,
            reply_markup=InlineKeyboardMarkup(out)
        )
        
        # LOGGER এ সেন্ড করা
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
    
    # গ্রুপের জন্য ESHANI স্টাইল ক্যাপশন
    caption_text = f"**🎵 {app.mention} IS ALIVE!**\n\n✨ **UPTIME:** `{get_readable_time(uptime)}`\n\n💫 **CLICK BELOW BUTTONS TO EXPLORE**"
    
    try:
        await send_start_video(
            client, message,
            caption_text=caption_text,
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
                caption_text=caption_text,
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
                        await message.reply_text("❌ This group is not allowed to play songs")
                        await app.send_message(LOGGER_ID, f"This group has been blacklisted automatically due to myanmar characters in the chat title, description or message \n Title:{ch.title} \n ID:{message.chat.id}")
                        return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                
                # ওয়েলকাম মেসেজ ESHANI স্টাইলে
                caption_text = f"**🎉 HEY {message.from_user.first_name}!**\n\n**✨ THANKS FOR ADDING ME IN «{message.chat.title}» ✨**\n\n🔗 **I CAN PLAY HIGH QUALITY MUSIC IN VOICE CHAT**\n\n💫 **USE /help TO GET STARTED**"
                
                await send_start_video(
                    client, message,
                    caption_text=caption_text,
                    reply_markup=InlineKeyboardMarkup(out)
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)