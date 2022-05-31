import os
import logging
import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from info import START_MSG, CHANNELS, ADMINS, AUTH_CHANNEL, CUSTOM_FILE_CAPTION, BOT_PICS
from utils import Media, get_file_details, get_size
from pyrogram.errors import UserNotParticipant
logger = logging.getLogger(__name__)

@Client.on_message(filters.command("start"))
async def start(bot, cmd):
    usr_cmdall1 = cmd.text
    if usr_cmdall1.startswith("/start subinps"):
        if AUTH_CHANNEL:
            invite_link = await bot.create_chat_invite_link(int(AUTH_CHANNEL))
            try:
                user = await bot.get_chat_member(int(AUTH_CHANNEL), cmd.from_user.id)
                if user.status == "kicked":
                    await bot.send_message(
                        chat_id=cmd.from_user.id,
                        text="Sorry Sir, You are Banned to use me.",
                        parse_mode="markdown",
                        disable_web_page_preview=True
                    )
                    return
            except UserNotParticipant:
                ident, file_id = cmd.text.split("_-_-_-_")
                await bot.send_photo(
                    chat_id=cmd.from_user.id,
                    photo=f"{random.choice(BOT_PICS)}",
                    caption="**Please Join My Updates Channel to use this Bot!**",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("🤖 Join Updates Channel", url=invite_link.invite_link)
                            ],
                            [
                                InlineKeyboardButton(" 🔄 Try Again", callback_data=f"checksub#{file_id}")
                            ]
                        ]
                    ),
                    parse_mode="markdown"
                )
                return
            except Exception:
                await bot.send_message(
                    chat_id=cmd.from_user.id,
                    text="Something went Wrong.",
                    parse_mode="markdown",
                    disable_web_page_preview=True
                )
                return
        try:
            ident, file_id = cmd.text.split("_-_-_-_")
            filedetails = await get_file_details(file_id)
            for files in filedetails:
                title = files.file_name
                size=get_size(files.file_size)
                f_caption=files.caption
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name=title, file_size=size, file_caption=f_caption)
                    except Exception as e:
                        print(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"@MovieSearchingBot"
                buttons = [
                    [
                        InlineKeyboardButton('Search Again', switch_inline_query_current_chat='')
                    ]
                    ]
                await bot.send_cached_media(
                    chat_id=cmd.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    reply_markup=InlineKeyboardMarkup(buttons)
                    )
        except Exception as err:
            await cmd.reply_text(f"Something went wrong!\n\n**Error:** `{err}`")
    elif len(cmd.command) > 1 and cmd.command[1] == 'subscribe':
        invite_link = await bot.create_chat_invite_link(int(AUTH_CHANNEL))
        await bot.send_photo(
            chat_id=cmd.from_user.id,
            photo=f"{random.choice(BOT_PICS)}",
            text="**Please Join My Updates Channel to use this Bot!**",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(" Join Updates Channel", url=invite_link.invite_link)
                    ]
                ]
            )
        )
    else:
        await bot.send_photo(
            photo=f"{random.choice(BOT_PICS)}",
            caption=START_MSG,
            parse_mode="Markdown",
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Search Here", switch_inline_query_current_chat=''),
                        InlineKeyboardButton('How to Use Me', url='https://t.me/movieReqGroup1')
                    ],
                    [
                        InlineKeyboardButton('Ｃｈａｎｎｅｌ', url='https://t.me/cinemacollections')
                    ]
                ]
            )
        )


@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('total') & filters.user(ADMINS))
async def total(bot, message):
    """Show total files in database"""
    msg = await message.reply("Processing...⏳", quote=True)
    try:
        total = await Media.count_documents()
        await msg.edit(f'📁 Saved files: {total}')
    except Exception as e:
        logger.exception('Failed to check total files')
        await msg.edit(f'Error: {e}')


@Client.on_message(filters.command('logger') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return

    result = await Media.collection.delete_one({
        'file_name': media.file_name,
        'file_size': media.file_size,
        'mime_type': media.mime_type
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        await msg.edit('File not found in database')
@Client.on_message(filters.command('about'))
async def bot_info(bot, message):
    buttons = [
        [
            InlineKeyboardButton('Ｃｈａｎｎｅｌ', url='https://t.me/cinemacollections'),
            InlineKeyboardButton('Ｇｒｏｕｐ', url='https://t.me/https://t.me/+vUrK_FA97m1hODAy')
        ]
        ]
    await message.reply(text="Language : <code>Python3</code>\nLibrary : <a href='https://docs.pyrogram.org/'>Pyrogram asyncio</a>\nSource Code : <a href='https://github.com'>Click here</a>\nUpdate Channel : <a href='https://t.me/CinemaCollections'>Update</a> </b>", reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

@Client.on_message(filters.command('help'))
async def bot_info(bot, message):
    buttons = [
        [
            InlineKeyboardButton('Ｃｈａｎｎｅｌ', url='https://t.me/Cinemacollections'),
            InlineKeyboardButton('Ｇｒｏｕｐ', url='https://t.me/movieReqGroup1')
        ]
        ]
    await message.reply(text="""🙋🏻‍♂️   Hellooo    <code> {user_name} 🤓</code>
       
▶️ ꜱᴇɴᴅ ᴛʜᴇ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ᴏꜰ мovιᴇ ꜱᴇʀɪᴇꜱ ( ᴜꜱᴇ ɢᴏᴏɢʟᴇ.ᴄᴏᴍ ᴛᴏ ɢᴇᴛ ᴄᴏʀʀᴇᴄᴛ ɴᴀᴍᴇ ! ) .
▫️ Exᴀᴍᴘʟᴇ 1 : Lᴜᴄɪꜰᴇʀ
▫️ Exᴀᴍᴘʟᴇ 2 : Lᴜᴄɪꜰᴇʀ мᴀʟᴀʏᴀʟᴀм
▫️ Exᴀᴍᴘʟᴇ 1 : Lᴜᴄɪꜰᴇʀ 2021
🔺 ɪꜰ ʏᴏᴜ ᴄᴀɴᴛ ꜰɪɴᴅ ᴛʜᴇ мovιᴇ ᴛʜᴀᴛ ʏᴏᴜ ʟᴏᴏᴋɪɴɢ ꜰᴏʀ. ᴛʜᴇɴ ʏᴏᴜ ᴄᴀɴ ꜱᴇɴᴅ ᴀ ᴍᴇꜱꜱᴀɢᴇ ᴛᴏ <a href='https://t.me/DhashamoolamDhamu'>Dᴇᴠ</a>""", reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=True)

