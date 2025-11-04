import json
from datetime import datetime
from pathlib import Path

def greeting_by_time_of_day() -> str:
    '''
    Функция возвращает строку с приветствием - «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
    в зависимости от текущего времени.
    :return string
    '''
    time_now = datetime.now().hour

    try:
        if 5 <= time_now < 12:
            return 'Доброе утро'
        elif 12 <= time_now < 17:
            return 'Добрый день'
        elif 17 <= time_now < 23:
            return 'Добрый вечер'
        else:
            return 'Доброй ночи'

    except Exception as er:
        print(f'Ошибка {er}')
        return 'Не могу определить время суток'


def get_first_day_of_month(date_str: str) -> str:
    """
    Функция возвращает первую дату месяца
    :param date_str: - дата запроса
    :return: первая дата месяца
    """
    date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    return str(date.replace(day=1, hour=0, minute=0, second=0))


def load_user_settings(file_path: str = '../user_settings.json') -> dict:
    '''
    Функция загружает пользовательские настройки из JSON файла
    :param file_path: путь к JSON файлу
    :return: словарь, с содержимым JSON файла
    '''
    path = Path(file_path)
    print(path)
    if not path.exists():
        print('Файл не найден')
        return {}
    else:
        with open(path, 'r', encoding="utf-8") as file:
            return json.load(file)

# print(load_user_settings())
