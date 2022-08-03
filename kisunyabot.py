"""
Модуль Telegram-бота, отправляющего изображения с кошками пользователю.

Отправление изображений осуществляется после запроса пользователя
на данное действие через кнопку "Подай котика!".

В случае, если API 'thecatapi' будет недоступен, предусмотрена возможность
отправки изображений с собаками через API 'thedogapi'.
"""

import logging
import os
import sys
from http import HTTPStatus
from json.decoder import JSONDecodeError

import requests
import telegram
from dotenv import load_dotenv
from telegram.ext import CommandHandler, Filters, MessageHandler, Updater

from exceptions import APIAnswerStatusCodeError, EnvVariableError

load_dotenv()

# Обязательная переменная окружения:
TELEGRAM_TOKEN = os.getenv('TOKEN')

# Настройки для запроса к API:
DEFAULT_ENDPOINT = 'https://api.thecatapi.com/v1/images/search'
BACKUP_ENDPOINT = 'https://api.thedogapi.com/v1/images/search'

# Настройка интерфейса бота:
BUTTON = 'Подай котика!'
MARKUP = telegram.ReplyKeyboardMarkup.from_button(BUTTON, resize_keyboard=True)

# Псевдонимы типов:
CustomContext = telegram.ext.callbackcontext.CallbackContext
CustomUpdate = telegram.update.Update


def init_logger() -> logging.Logger:
    """Инициализация логгера."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] - %(message)s'
    ))
    logger.addHandler(handler)

    logger.info('Инициализация логгера выполнена успешно.')
    return logger


logger = init_logger()


def send_message(context: CustomContext, chat_id: int, text: str) -> None:
    """Отправка сообщения пользователю."""
    try:
        context.bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=MARKUP
        )
        logger.info(f'Сообщение "{text}" отправлено успешно.')
    except Exception as error:
        logger.error(f'Неудачная попытка отправить сообщение "{text}" '
                     f'пользователю. Ошибка: {error}.')


def parse_answer(response: requests.models.Response) -> str:
    """Проверка ответа от API на корректность и получение URL изображения."""
    try:
        response = response.json()
    except JSONDecodeError as error:
        text = 'Эндпоинт передал ответ не в формате json.'
        logger.error(text)
        raise error(text)

    if not isinstance(response, list):
        text = ('Неверный тип данных декодированного из json ответа. '
                f'Требуется список, текущий тип - {type(response)}.')
        logger.error(text)
        raise TypeError(text)
    if not response:
        text = 'Декодированный из json ответ ошибочно пуст.'
        logger.error(text)
        raise ValueError(text)

    response_information = response[0]

    if not isinstance(response_information, dict):
        text = ('Неверный тип данных элемента ответа. Требуется словарь, '
                f'текущий тип - {type(response_information)}.')
        logger.error(text)
        raise TypeError(text)
    if 'url' not in response_information:
        text = 'Ответ не содержит данные про "url".'
        logger.error(text)
        raise KeyError(text)

    logger.info('Проверка ответа от API на корректность выполнена успешно.')
    return response_information['url']


def get_response() -> requests.models.Response:
    """Получение ответа от API."""
    try:
        response = requests.get(DEFAULT_ENDPOINT)
        if response.status_code != HTTPStatus.OK:
            text = (f'Эндпоинт {DEFAULT_ENDPOINT} недоступен. '
                    f'Код ответа API: {response.status_code}.')
            logger.error(text)
            raise APIAnswerStatusCodeError(text)
        logger.info('Запрос к основному API выполнен успешно.')
    except Exception as error:
        logger.error(f'Ошибка при запросе к основному API: {error}')
        logger.debug('Попытка обратиться к запасному API')
        response = requests.get(BACKUP_ENDPOINT)
        if response.status_code != HTTPStatus.OK:
            text = (f'Эндпоинт {BACKUP_ENDPOINT} недоступен. '
                    f'Код ответа API: {response.status_code}.')
            logger.error(text)
            raise APIAnswerStatusCodeError(text)
        logger.info('Запрос к запасному API выполнен успешно.')
    return response


def new_image(update: CustomUpdate, context: CustomContext) -> None:
    """Логика работы хендлера сообщения по кнопке."""
    logger.debug(f'Получено сообщение "{update.message.text}"')
    chat = update.effective_chat
    try:
        response = get_response()
        image = parse_answer(response)
        context.bot.send_photo(chat.id, image)
        logger.info('Изображение на сообщение по кнопке отправлено успешно.')
    except Exception as error:
        logger.error('Сбой в работе программы при ответе на сообщение '
                     f'по кнопке: {error}')
        text = ('К сожалению, сервис на данный момент недоступен. '
                'Попробуйте обратиться позднее.')
        send_message(context=context, chat_id=chat.id, text=text)


def reply_to_message(update: CustomUpdate, context: CustomContext) -> None:
    """Логика работы хендлера любого сообщения (кроме сообщения по кнопке)."""
    logger.debug(f'Получено сообщение "{update.message.text}"')
    chat = update.effective_chat
    text = ('К сожалению, я не умею общаться. Но зато мастерски ищу '
            'фотографии котиков.')
    send_message(context=context, chat_id=chat.id, text=text)


def wake_up(update: CustomUpdate, context: CustomContext) -> None:
    """Логика работы командного хендлера 'start'."""
    logger.debug(f'Получено сообщение "{update.message.text}"')
    chat = update.effective_chat
    name = chat.first_name
    text = f'Привет, {name}. Посмотри, какого котика я тебе нашёл!'
    send_message(context=context, chat_id=chat.id, text=text)

    try:
        response = get_response()
        image = parse_answer(response)
        context.bot.send_photo(chat.id, image)
        logger.info('Изображение на команду "start" отправлено успешно.')
    except Exception as error:
        logger.error('Сбой в работе программы при ответе на командное '
                     f'сообщение "start": {error}')
        text = ('К сожалению, сервис на данный момент недоступен. '
                'Попробуйте обратиться позднее.')
        send_message(context=context, chat_id=chat.id, text=text)


def check_token() -> bool:
    """Проверка доступности обязательной переменной окружения."""
    if TELEGRAM_TOKEN:
        logger.info('Проверка доступности обязательной переменной окружения '
                    'проведена успешно.')
        return True
    logger.critical(
        ('Отсутствует обязательная переменная окружения. '
         'Программа будет принудительно остановлена.')
    )
    return False


def main() -> None:
    """Основная логика работы бота."""
    if check_token() is False:
        raise EnvVariableError

    updater = Updater(token=TELEGRAM_TOKEN)

    updater.dispatcher.add_handler(CommandHandler('start', wake_up))
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text(BUTTON), new_image)
    )
    updater.dispatcher.add_handler(
        MessageHandler(Filters.text, reply_to_message)
    )

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
