from datetime import datetime


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

