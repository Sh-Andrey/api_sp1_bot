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
    format='%(asctime)s, %(levelname)s, %(name)s, %(message)s'
)
logger = logging.getLogger('__name__')
handler = RotatingFileHandler('bot.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)
try:
    f = open('bot.log')
    f.close()
except FileNotFoundError:
    print('Файл с логами не найден.')

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
try:
    os.environ['TELEGRAM_TOKEN']
except KeyError:
    logging.error('Не удалось получить токен бота.')

CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
try:
    os.environ['TELEGRAM_CHAT_ID']
except KeyError:
    logging.error('Не удалось получить токен чата.')

BOT = telegram.Bot(token=TELEGRAM_TOKEN)
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

    if homework_name is None:
        logging.error('Не удалось получить данные.')
        return 'Не удалось получить данные.'
    if homework_status is None:
        logging.error('Не удалось получить данные.')
        return 'Не удалось получить данные.'

    if homework_status == 'reviewing':
        return STATUS['reviewing']
    elif homework_status == 'rejected':
        verdict = STATUS['rejected']
    elif homework_status == 'approved':
        verdict = STATUS['approved']
    else:
        logging.error('Получен незвестный статус.')
        return 'Получен незвестный статус.'
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
    except requests.HTTPError as error:
        logging.error(f'{BOT_ERROR}{error}', exc_info=True)
        send_message(f'{BOT_ERROR}{error}', BOT)
    except KeyError as error:
        logging.error(f'{BOT_ERROR}{error}', exc_info=True)
        send_message(f'{BOT_ERROR}{error}', BOT)
    except requests.RequestException as error:
        logging.error(f'{BOT_ERROR}{error}', exc_info=True)
        send_message(f'{BOT_ERROR}{error}', BOT)
    return homework_statuses


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    current_timestamp = int(time.time())
    logging.debug('Бот запущен.')
    send_message('Бот запущен.', BOT)
    try:
        os.environ['PRAKTIKUM_TOKEN']
    except KeyError:
        logging.error('Не удалось получить токен Яндекс Практики.')
        send_message('Не удалось получить токен Яндекс Практики.', BOT)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                send_message(
                    parse_homework_status(
                        new_homework.get('homeworks')[0]), BOT
                )
                logging.info('Бот отправил сообщение.')
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )

            time.sleep(300)

        except Exception as error:
            logging.error(f'{BOT_ERROR}{error}', exc_info=True)
            send_message(f'{BOT_ERROR}{error}', BOT)
            time.sleep(5)


if __name__ == '__main__':
    main()
