import json
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any

import pandas as pd
from pandas import DataFrame


def greeting_by_time_of_day() -> str:
    """
    Функция возвращает строку с приветствием - «Доброе утро» / «Добрый день» / «Добрый вечер» / «Доброй ночи»
    в зависимости от текущего времени.
    :return string
    """
    time_now = datetime.now().hour

    try:
        if 5 <= time_now < 12:
            return "Доброе утро"
        elif 12 <= time_now < 17:
            return "Добрый день"
        elif 17 <= time_now < 23:
            return "Добрый вечер"
        else:
            return "Доброй ночи"

    except Exception as er:
        print(f"Ошибка {er}")
        return "Не могу определить время суток"


def get_first_day_of_month(date_str: str) -> str:
    """
    Функция возвращает первую дату месяца
    :param date_str: - дата запроса
    :return: первая дата месяца
    """
    date = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
    date = date.replace(day=1, hour=0, minute=0, second=0)
    date_format = str(date.strftime("%d.%m.%Y %H:%M:%S"))
    return date_format


def load_user_settings(file_path: str = "../user_settings.json") -> dict[Any, Any]:
    """
    Функция загружает пользовательские настройки из JSON файла
    :param file_path: путь к JSON файлу
    :return: словарь, с содержимым JSON файла
    """
    path = Path(file_path)
    print(path)
    if not path.exists():
        print("Файл не найден")
        return {}
    else:
        with open(path, "r", encoding="utf-8") as file:
            return dict(json.load(file))


def get_operation_for_period_from_excel(
    file_path: str = "../data/operations.xlsx", curr_date: str = "10.10.2021 10:10:10"
) -> DataFrame:
    """
    Функция принимает путь к EXCEL файлу и дату и возвращает таблицу с операциями с начала месяца по полученую дату
    :param file_path: путь к EXCEL файлу
    :param curr_date: необходимая дата
    :return:
    """
    try:
        df = pd.read_excel(file_path, sheet_name="Отчет по операциям")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        first_day_of_month = datetime.strptime(get_first_day_of_month(curr_date), "%d.%m.%Y %H:%M:%S")

        necessary_date = datetime.strptime(curr_date, "%d.%m.%Y %H:%M:%S")
        filter_df_by_date = df[(df["Дата операции"] >= first_day_of_month) & (df["Дата операции"] <= necessary_date)]
        return filter_df_by_date
    except FileNotFoundError:
        print("Файл не найден")
    except ValueError as er:
        print(f"Лист с указанным именем не найден {er}")
    except Exception as er:
        print(f"Ошибка при чтении файла: {str(er)}")


# print(get_first_day_of_month('10.10.2020 10:10:10'))

pprint(get_operation_for_period_from_excel())
