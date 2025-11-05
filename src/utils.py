import json
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Any, Dict, List

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()

API_KEY_EXCHANGE: str | None = os.getenv("API_KEY_EXCHANGE")


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


def get_expenses_by_card(filtered_df: pd.DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame с операциями и возвращает список словарей с суммарными расходами и суммарным
    кэшбэком по каждой карте
    :param filtered_df: DataFrame c операциями
    :return:
    """
    try:
        filtered_df["Номер карты"] = filtered_df["Номер карты"].str.replace(r"\D", "", regex=True)
        expenses_df = filtered_df[filtered_df["Сумма операции"] < 0]
        result_expenses = (
            expenses_df.groupby("Номер карты")
            .agg(total_expenses=("Сумма операции с округлением", "sum"), cashback=("Кэшбэк", "sum"))
            .reset_index()
        )
        result_expenses.columns = ["card_num", "total_expenses", "cashback"]
        return result_expenses.to_dict(orient="records")

    except ValueError as ve:
        print(ve)
        return []


def get_top5_transaction(filtered_df: pd.DataFrame) -> List[Dict]:
    """
    Функция получает DataFrame с транзакциями и возвращает список топ-5
    :param filtered_df:
    :return:
    """
    try:
        top_5 = filtered_df.sort_values(by="Сумма операции с округлением", ascending=False).head(5)
        columns = ["Дата платежа", "Сумма операции", "Категория", "Описание"]
        top_5_transactions = top_5[columns]
        top_5_transactions.columns = ["date", "amount", "category", "description"]
        return top_5_transactions.to_dict(orient="records")
    except Exception as ex:
        print(ex)


def get_currency_rate() -> List[Dict]:
    """
    Функция возвращает список с курсами валют
    """
    user_currency: list = load_user_settings()["user_currencies"]
    print(user_currency)
    result = []
    headers: dict = {"apikey": API_KEY_EXCHANGE}
    print(headers)
    for currency in user_currency:
        try:
            resp = requests.request(
                "GET",
                f"https://api.apilayer.com/exchangerates_data/latest?symbols=RUB&base={currency}",
                headers=headers,
                data={},
            )
            data = resp.json()
            rate = data.get("rates", {}).get("RUB")
            result.append({"currency": currency, "rates": round(rate, 2)})
        except Exception as e:
            print(e)
    return result


def get_stock_prices() -> List[Dict]:
    """
    Функция возвращает стоимость акций из списка в файле user_settings.json
    """
    user_stocks: list = load_user_settings()["user_stocks"]
    data = yf.Tickers(user_stocks)
    stock_prices_list = []

    for stock in data.tickers:
        try:
            stock_info = {"stock": stock, "price": round(data.tickers[stock].info["currentPrice"], 2)}

            stock_prices_list.append(stock_info)

        except KeyError as ke:
            print(f"Отсутствуют данные для {stock}: {ke}")
        except Exception as e:
            print(f"Ошибка при получении данных для {stock}: {e}")
    return stock_prices_list


# print(get_first_day_of_month('10.10.2020 10:10:10'))

# get_expenses_by_card(get_operation_for_period_from_excel())
# get_top5_transaction(get_operation_for_period_from_excel())
# pprint(get_top5_transaction(get_operation_for_period_from_excel()))
# print(get_currency_rate())
print(get_stock_prices())
