import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()

LOG_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(LOG_DIR, 'bot.log')

handler = RotatingFileHandler(LOG_PATH,
                              mode='w',
                              maxBytes=1000000,
                              backupCount=3)
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] => %(message)s',
    handlers=[handler]
)

BOT_START = 'Бот запущен.'
BOT_SENT = 'Бот отправил сообщение. '
BOT_ERROR = 'Бот столкнулся с ошибкой: '
STATUS_ERROR = 'Получен незвестный статус.'
THERE_IS_NO_DATA = 'Не удалось получить данные.'
BOT_ERROR_TOKEN = 'Не удалось получить токены. Бот остановлен.'

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.critical(BOT_ERROR_TOKEN)
    raise SystemExit(BOT_ERROR_TOKEN)

HOMEWORK_STATUSES = {
    'rejected': 'К сожалению в работе нашлись ошибки.',
    'reviewing': 'Работа взята в ревью.',
    'approved': 'Ревьюеру всё понравилось,'
                ' можно приступать к следующему уроку.'
}

PRAKTIKUM_API = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
HEADER = {
    'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
}


def parse_homework_status(homework):
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_name is None or homework_status is None:
        logging.error(THERE_IS_NO_DATA)
        return THERE_IS_NO_DATA

    if homework_status not in HOMEWORK_STATUSES:
        logging.error(STATUS_ERROR)
        return STATUS_ERROR

    if homework_status == 'reviewing':
        return HOMEWORK_STATUSES[homework_status]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    if current_timestamp is None:
        current_timestamp = int(time.time())

    from_date = {
        'from_date': current_timestamp
    }
    try:
        homework_statuses = requests.get(
            url=PRAKTIKUM_API,
            headers=HEADER,
            params=from_date
        )
        homework_statuses = homework_statuses.json()
    except (requests.exceptions.RequestException,
            json.JSONDecodeError) as error:
        logging.error(f'{BOT_ERROR}{error}', exc_info=True)
    return homework_statuses


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(BOT_START)
    send_message(BOT_START, bot)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            homework = new_homework.get('homeworks')
            if homework:
                parse_status = parse_homework_status(homework[0])
                send_message(parse_status, bot)
                logging.info(f'{BOT_SENT}{parse_status}')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )

            time.sleep(300)

        except Exception as error:
            logging.error(f'{BOT_ERROR}{error}', exc_info=True)
            send_message(f'{BOT_ERROR}{error}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
