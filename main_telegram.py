from telegram.ext import Updater, CommandHandler, Job, MessageHandler, Filters, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import telegram
import threading
import logging
import typing
import sys
import json
import re
import os

from utils import make_plot, myThread

counter = 0

info_text = []
info_text.append('You can control me by sending these commands:')
info_text.append('')
info_text.append('/ibmqx4 - statistics for ibmqx4 quantum processor')
info_text.append('/ibmqx5 - statistics for ibmqx5 quantum processor')
info_text = '\n'.join(info_text)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - \
                            %(message)s', level=logging.INFO)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def get_token():
    path = os.path.join('res', 'token_telegram.json')
    with open(path) as jsn:
        data = json.load(jsn)
    return data['token']


def choose_backend(bot, update):
    global counter
    counter += 1

    backends = ['ibmqx4', 'ibmqx5']
    backend = update.message.text[1:]

    if backend in backends:
        create_statistics_image(backend)

        user_id = update.message.chat_id
        bot.send_photo(chat_id=user_id, photo=open('{}_to_send.png'.format(backend), 'rb'))
    else:
        update.message.reply_text(info_text)


def info(bot, update):
    update.message.reply_text(counter)


def help(bot, update):
    update.message.reply_text(info_text)


def main():
    updater = Updater(get_token())

    bot = telegram.Bot(token=get_token())
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('help', help))
    dp.add_handler(CommandHandler('info', info))
    dp.add_handler(CommandHandler('start', help))
    dp.add_handler(MessageHandler(Filters.text, help))
    dp.add_handler(MessageHandler(Filters.command, choose_backend))

    # Start dumper.
    run_event = threading.Event()
    run_event.set()
    # Create new threads.
    delay = 60  # Seconds.
    thread = myThread(delay, run_event)
    thread.start()
    ########

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
