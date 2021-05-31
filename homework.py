import logging
import os
import time

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

PRAKTIKUM_TOKEN = os.getenv('PRAKTIKUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def parse_homework_status(homework):
    if homework.get('homework_name', 'status') is None:
        logging.error('Не удалось получить данные.')
        return 'Не удалось получить данные.'

    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if homework_status == 'rejected':
        verdict = 'К сожалению в работе нашлись ошибки.'
    elif homework_status == 'reviewing':
        verdict = 'Работа взята в ревью.'
    elif homework_status == 'approved':
        verdict = 'Ревьюеру всё понравилось, ' \
                  'можно приступать к следующему уроку.'
    return f'У вас проверили работу "{homework_name}"!\n\n{verdict}'


def get_homework_statuses(current_timestamp):
    api = 'https://praktikum.yandex.ru/api/user_api/homework_statuses/'
    header = {
        'Authorization': f'OAuth {PRAKTIKUM_TOKEN}'
    }
    from_date = {
        'from_date': current_timestamp
    }
    try:
        homework_statuses = requests.get(
            url=api,
            headers=header,
            params=from_date
        )
        return homework_statuses.json()
    except requests.RequestException as error:
        logging.error(f'Бот столкнулся с ошибкой: {error}', exc_info=True)


def send_message(message, bot_client):
    return bot_client.send_message(chat_id=CHAT_ID, text=message)


def main():
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    logging.debug('Бот запущен.')
    send_message('Бот запущен.', bot)

    while True:
        try:
            new_homework = get_homework_statuses(current_timestamp)
            if new_homework.get('homeworks'):
                logging.info('Бот отправил сообщение.')
                send_message(parse_homework_status(
                    new_homework.get('homeworks')[0]), bot
                )
            current_timestamp = new_homework.get(
                'current_date', current_timestamp
            )
            time.sleep(300)

        except Exception as error:
            logging.error(f'Бот столкнулся с ошибкой: {error}', exc_info=True)
            send_message(f'Бот столкнулся с ошибкой: {error}', bot)
            time.sleep(5)


if __name__ == '__main__':
    main()
