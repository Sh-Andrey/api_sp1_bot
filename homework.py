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
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] => %(message)s',
    handlers=[handler]
)

BOT_STATUSES = {
    'start': 'Бот запущен.',
    'sent': 'Бот отправил сообщение. ',
    'error': 'Бот столкнулся с ошибкой: ',
    'error_token': 'Не удалось получить токены. Бот остановлен.',
    'there_is_no_data': 'Не удалось получить данные.',
    'status_error': 'Получен незвестный статус.'
}

try:
    PRAKTIKUM_TOKEN = os.environ['PRAKTIKUM_TOKEN']
    TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
    CHAT_ID = os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.critical(BOT_STATUSES['error_token'])
    raise SystemExit(BOT_STATUSES['error_token'])

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
        logging.error(BOT_STATUSES['there_is_no_data'])
        return BOT_STATUSES['there_is_no_data']

    if homework_status not in HOMEWORK_STATUSES:
        logging.error(BOT_STATUSES['status_error'])
        return BOT_STATUSES['status_error']

    if homework_status == 'reviewing':
        return HOMEWORK_STATUSES[homework_status]
    verdict = HOMEWORK_STATUSES[homework_status]
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    current_timestamp = current_timestamp or int(time.time())
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
        logging.error(f'{BOT_STATUSES["error"]}{error}', exc_info=True)
        return f'{BOT_STATUSES["error"]}{error}'
    return homework_statuses


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    logging.info(BOT_STATUSES['start'])

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if isinstance(new_homework, str):
                new_homework.startswith(BOT_STATUSES['error'])
                send_message(new_homework, bot)
                time.sleep(300)
                continue
            homework = new_homework.get('homeworks')
            if not homework:
                continue
            if homework is not None:
                parse_status = parse_homework_status(homework[0])
                send_message(parse_status, bot)
                logging.info(f'{BOT_STATUSES["sent"]}{parse_status}')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )

            time.sleep(300)

        except Exception as error:
            logging.error(f'{BOT_STATUSES["error"]}{error}', exc_info=True)
            send_message(f'{BOT_STATUSES["error"]}{error}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
