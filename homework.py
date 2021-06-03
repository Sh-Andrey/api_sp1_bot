import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.DEBUG,
    filename='bot.log',
    filemode='w',
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s',
)
handler = RotatingFileHandler('bot.log', maxBytes=50000000, backupCount=5)

try:
    f = open('bot.log')
    f.close()
except FileNotFoundError:
    print('Файл с логами не найден.')

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.error('Не удалось получить токены.')
    SystemExit(1)


BOT_START = 'Бот запущен.'
BOT_ERROR = 'Бот столкнулся с ошибкой: '

STATUS = {
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
        logging.error('Не удалось получить данные.')
        return 'Не удалось получить данные.'

    if homework_status not in STATUS:
        logging.error('Получен незвестный статус.')
        return 'Получен незвестный статус.'

    if homework_status == 'reviewing':
        return STATUS[homework_status]
    if homework_status in STATUS:
        verdict = STATUS[homework_status]
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
    current_timestamp = 0
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.debug(BOT_START)
    send_message(BOT_START, bot)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)

            if new_homework.get('homeworks'):
                homework_get = new_homework.get('homeworks')[0]
                parse_status = parse_homework_status(homework_get)
                send_message(parse_status, bot)
                logging.info(f'Бот отправил сообщение. {parse_status}')
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
