import datetime
from pymongo import MongoClient
from pyrogram.errors import FloodWait, InputUserDeactivated, UserIsBlocked, PeerIdInvalid
import asyncio
import traceback
import os

BROADCAST_DB_URL = os.environ.get('BROADCAST_DB_URL',False)

if not BROADCAST_DB_URL:
    raise "SET BROADCAST_DB_URL in var with a mongo db url"

SESSION_NAME = ""
broadcast_ids = {}


class Database:

    def __init__(self, uri, database_name):
        self.cluster = MongoClient(uri)
        self.db = self.cluster[database_name]
        self.col = self.db.users

    def new_user(self, id):
        return dict(
            id=id,
            broadcast_enabled=True,
            join_date=datetime.date.today().isoformat()
        )

    async def add_user(self, id):
        user = self.new_user(id)
        self.col.insert_one(user)

    async def del_user(self, id):
        user = self.col.find_one({'id': int(id)})
        if user:
            self.col.delete_one({'id': int(id)})
            return True
        else:
            return False

    async def is_user_exist(self, id):
        user = self.col.find_one({'id': int(id)})
        return True if user else False

    async def total_users_count(self):
        count = self.col.count_documents({})
        return count

    async def get_all_users(self):
        all_users = self.col.find({})
        return all_users

    async def get_all_enabled_users(self):
        all_users = self.col.find({'broadcast_enabled': True})
        return all_users

    async def get_settings(self, id):
        user = self.col.find_one({'id': int(id)})
        return user['broadcast_enabled']

    async def toogle_broadcast(self, id, value):
        user = self.col.update_one({'id': int(id)}, {"$set": {'broadcast_enabled': value}})


db = Database(BROADCAST_DB_URL, 'MediaSearchBroadcast')


async def send_msg(user_id, message):
    try:
        if message.poll:
            await message.forward(chat_id=user_id)
            return 200, None
        else:
            await message.copy(chat_id=user_id)
            return 200, None
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return send_msg(user_id, message)
    except InputUserDeactivated:
        return 400, f"{user_id} : deactivated\n"
    except UserIsBlocked:
        return 400, f"{user_id} : blocked the bot\n"
    except PeerIdInvalid:
        return 400, f"{user_id} : user id invalid\n"
    except Exception as e:
        return 500, f"{user_id} : {traceback.format_exc()}\n"