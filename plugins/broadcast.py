from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from broadcast_db import db, send_msg
from pyrogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import datetime
import asyncio
import string
import aiofiles
import aiofiles.os
import time
import random
from info import ADMINS

broadcast_ids = {}

@Client.on_message(filters.private, group=5)
async def add_user_todb(c:Client,message: Message):
    user_id = message.from_user.id
    if not await db.is_user_exist(user_id):
        await db.add_user(user_id)


@Client.on_message(filters.private & filters.command('settings'))
async def sed_settings(c:Client,message: Message):
    user_id = message.from_user.id
    settings = await db.get_settings(user_id)
    if settings:
        txt = "Broadcast is Currently Enabled for you"
        btn = [[InlineKeyboardButton('Disable Broadcast', callback_data="broadcast|disable")]]
    else:
        txt = "Broadcast is Currently Disabled for you"
        btn = [[InlineKeyboardButton('Enable Broadcast', callback_data="broadcast|enable")]]
    await message.reply(txt,reply_markup=InlineKeyboardMarkup(btn))


@Client.on_callback_query(filters.regex('^broadcast\|(enable|disable)$'), group= 5)
async def toogle_cast(c:Client, update:CallbackQuery):
    user_id = update.from_user.id
    typ = update.data.split('|',1)[1]
    if typ == 'enable':
        await db.toogle_broadcast(user_id,True)
        txt = "Broadcast is Currently Enabled for you"
        btn = [[InlineKeyboardButton('Disable Broadcast', callback_data="broadcast|disable")]]
    else:
        await db.toogle_broadcast(user_id, False)
        txt = "Broadcast is Currently Disabled for you"
        btn = [[InlineKeyboardButton('Enable Broadcast', callback_data="broadcast|enable")]]
    await update.edit_message_text(txt,reply_markup=InlineKeyboardMarkup(btn))


@Client.on_message(filters.command('subcount') & filters.user(ADMINS) & filters.private)
async def get_users(client: Client, message: Message):
    msg = await client.send_message(chat_id=message.chat.id, text="Counting Users....")
    total_users = await db.total_users_count()
    enabled_users = len(list(await db.get_all_enabled_users()))
    await msg.edit(text=f"Total user(s) using Bot - {total_users}\nTotal user(s) enbled Broadcast - {enabled_users}")


@Client.on_message(filters.command('broadcast') & filters.user(ADMINS) & filters.private)
async def broadcast(client: Client, message: Message):
    reply_markup = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton("Cancel"), KeyboardButton("Confirm")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply("Send the message that you want to Broadcast")
    response = await client.listen(chat_id=message.chat.id)
    await response.copy(message.chat.id)
    await client.send_message(chat_id=message.chat.id, text="Do you want to send the Broadcast", reply_markup=reply_markup)
    while True:
        confirm = await client.listen(chat_id=message.chat.id)
        if confirm.text == "Cancel":
            break
        elif confirm.text == "Confirm":
            break
        else:
            continue
    if not confirm.text == "Confirm":
        await client.send_message(chat_id=message.chat.id, text=f"Broadcast Cancelled",
                                  reply_markup=ReplyKeyboardRemove())
        return
    await client.send_message(chat_id=message.chat.id, text="Sending Broadcast",
                              reply_markup=ReplyKeyboardRemove())
    all_users = await db.get_all_enabled_users()

    while True:
        broadcast_id = ''.join([random.choice(string.ascii_letters) for i in range(3)])
        if not broadcast_ids.get(broadcast_id):
            break

    start_time = time.time()
    total_users = len(list(await db.get_all_enabled_users()))
    done = 0
    failed = 0
    success = 0

    broadcast_ids[broadcast_id] = dict(
        total=total_users,
        current=done,
        failed=failed,
        success=success
    )
    async with aiofiles.open('broadcast.txt', 'w') as broadcast_log_file:
        for user in all_users:

            sts, msg = await send_msg(
                user_id=int(user['id']),
                message=response
            )
            if msg is not None:
                await broadcast_log_file.write(msg)

            if sts == 200:
                success += 1
            else:
                failed += 1

            if sts == 400:
                await db.del_user(user['id'])

            done += 1
            if broadcast_ids.get(broadcast_id) is None:
                break
            else:
                broadcast_ids[broadcast_id].update(
                    dict(
                        current=done,
                        failed=failed,
                        success=success
                    )
                )
    if broadcast_ids.get(broadcast_id):
        broadcast_ids.pop(broadcast_id)
    completed_in = datetime.timedelta(seconds=int(time.time() - start_time))

    await asyncio.sleep(3)

    if failed == 0:
        await message.reply_text(
            text=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed."
        )
    else:
        await message.reply_document(
            document='broadcast.txt',
            caption=f"Broadcast completed in `{completed_in}`\n\nTotal users {total_users}.\nTotal done {done}, {success} success and {failed} failed."
        )

    await aiofiles.os.remove('broadcast.txt')