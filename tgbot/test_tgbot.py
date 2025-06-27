import json
import os, glob
import asyncio
import logging


from datetime import datetime
from aiogram import Bot
from aiogram import Dispatcher
from aiogram import types

with open("C:\\Users\\Vanya\\Desktop\\myRepo\\data.json", "r",encoding='utf-8') as f:
    data = json.load(f)
    print(data)
    t = data["token"]
    print(t)

bot = Bot(token=t)
dp = Dispatcher()
list_greetings = ["Привет", "привет","ghbdtn","Ghbdtn"]
@dp.message()
async def echo_message(message: types.Message):
    print(message)
    await bot.send_message(
        chat_id=message.chat.id,
        text="Подожди секундну..."
    )
    #await message.answer(text=message.text)
    if message.text:
        print(message.chat.username + ":" + message.text)
        if message.text in list_greetings:
            await message.reply(text="Привет! Что ты хочешь сделать?")
        else:
            await message.reply(text="Напиши , куда ты хочешь записаться ?")
    else:
        await message.reply(
            text="Не смог разобрать :( Попробуй написать Привет"
        )


async def main():
    logging.basicConfig(level=logging.INFO)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
