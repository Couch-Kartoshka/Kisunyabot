# Telegram бот @kisunyabot (Повелитель кошек)
Модуль Telegram-бота, отправляющего неповторяющиеся изображения с кошками пользователю.
***
## Особенности модуля:
- Отправление изображений осуществляется после запроса пользователя на данное действие через кнопку "Подай котика!".
- Получение изображений осуществляется через API https://thecatapi.com.
- В случае, если API 'thecatapi' будет недоступен, предусмотрена возможность отправки изображений с собаками через API 'thedogapi' (https://www.thedogapi.com).

## Необходимые для работы переменные окружения:
- TELEGRAM_TOKEN - токен Telegram бота

## Используемый стек:
- Python 3.8.9
- python-telegram-bot 13.7

## Автор:
Кира Изгагина