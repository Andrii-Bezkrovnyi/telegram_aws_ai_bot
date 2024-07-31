import os
import textwrap

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from aiogram import F
from dotenv import load_dotenv
from loguru import logger

from ai_bot import create_db_from_url, get_response_from_query

load_dotenv()
logger.add("bot_info.log", level="INFO", format="{time} - {level} - {message}")

# Set your TELEGRAM TOKEN key here
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN isn't set")

# Create bot and dispatcher objects
bot = Bot(token=TELEGRAM_BOT_TOKEN)
dp = Dispatcher()
logger.info("AI Bot is starting!")

# This handler will be triggered by the "/start" command
@dp.message(Command(commands=["start"]))
async def process_start_command(message: Message) -> None:
    """
    Handles the /start command, providing an introductory message to the user.

    Args:
        message (Message): The incoming message object from the user.
    """
    await message.answer('Hello!\n'
                         'I am AI Bot!\n'
                         'I can help you with information about Amazon`s return policy.\n'
                         'Please, enter your questions only about this topic.\n\n'
                         'You can also get more information'
                         'about my functionality using command /help.\n')


# This handler will be triggered by the "/help" command
@dp.message(Command(commands=['help']))
async def process_help_command(message: Message) -> None:
    """
    Handles the /help command, providing information about the bot's functionality.

    Args:
        message (Message): The incoming message object from the user.
    """
    await message.answer(
        'Hey!I am AI Bot!\n'
        'I have a lot information about Amazon`s return policy.\n'
        'But I can answer  only questions about Amazon`s return policy.\n'
        'Please, enter your questions only in this sphere.\n\n'
        'You can use command /start for began my work.\n'
        'And you can use command /help for getting more information'
        'about my functionality.\n')


# This handler will work on any of your text messages,
# except for the "/start" and "/help" commands
@dp.message()
async def send_answer(message: Message) -> None:
    """
    Handles any text message that isn't a command, processing the user's query
    and responding with relevant information.

    Args:
        message (Message): The incoming message object from the user.
    """
    db = create_db_from_url()
    if db is None:
        await message.reply(text="Sorry, I couldn't process your request at this time. Please try again later.")
        return None

    user_query = message.text
    response, docs = get_response_from_query(db, user_query)
    bot_answer = textwrap.fill(response, width=85)
    logger.info('The answer is displaying...')
    await message.reply(text=bot_answer)


if __name__ == '__main__':
    dp.run_polling(bot)
