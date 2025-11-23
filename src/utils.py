import json
import logging
import os
from datetime import datetime
from pathlib import Path
from pprint import pprint
from typing import Dict, List

import pandas as pd
import requests
import yfinance as yf
from dotenv import load_dotenv
from pandas import DataFrame

load_dotenv()
API_KEY_EXCHANGE: str | None = os.getenv("API_KEY_EXCHANGE")

logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)
current_dir = Path(__file__).parent
root_dir = current_dir.parent
path = root_dir / "logs/utils.log"
file_handler = logging.FileHandler(path, mode="w", encoding="utf-8")
file_formater = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s: %(message)s")
file_handler.setFormatter(file_formater)
logger.addHandler(file_handler)


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
        logger.error(f"Ошибка {er}")
        return "Не могу определить время суток"


def get_first_day_of_month(date_str: str) -> str:
    """
    Функция возвращает первую дату месяца
    :param date_str: - дата запроса
    :return: первая дата месяца
    """
    date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    date = date.replace(day=1, hour=0, minute=0, second=0)
    date_format = str(date.strftime("%Y-%m-%d %H:%M:%S"))
    return date_format


def load_user_settings(file_path: str = "user_settings.json") -> dict:
    """
    Функция загружает пользовательские настройки из JSON файла
    :param file_path: путь к JSON файлу
    :return: словарь, с содержимым JSON файла
    """
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent
    path = root_dir / file_path
    if not path.exists():
        logger.error("Файл пользовательскими данными не найден")
        return {}
    else:
        with open(path, "r", encoding="utf-8") as file:
            logger.info(f"Открыт файл с пользовательскими настройками: {file_path}")
            return dict(json.load(file))


def get_operation_for_period_from_excel(
    file_path: str = "data/operations.xlsx", curr_date: str = "2021-08-20 15:30:00"
) -> DataFrame:
    """
    Функция принимает путь к EXCEL файлу и дату и возвращает таблицу с операциями с начала месяца по полученую дату
    :param file_path: путь к EXCEL файлу
    :param curr_date: необходимая дата
    :return:
    """
    current_dir = Path(__file__).parent
    root_dir = current_dir.parent
    path = root_dir / file_path
    try:
        df = pd.read_excel(path, sheet_name="Отчет по операциям")
        logger.info(f"Прочитан файл {path}")
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], dayfirst=True)
        first_day_of_month = datetime.strptime(get_first_day_of_month(curr_date), "%Y-%m-%d %H:%M:%S")

        necessary_date = datetime.strptime(curr_date, "%Y-%m-%d %H:%M:%S")
        filter_df_by_date = df[(df["Дата операции"] >= first_day_of_month) & (df["Дата операции"] <= necessary_date)]
        return filter_df_by_date
    except FileNotFoundError:
        logger.error("Файл с операциями не найден")
    except ValueError as er:
        logger.error(f"Неверный формат даты: {er}")
        raise
    except Exception as er:
        logger.error(f"Ошибка при чтении файла: {str(er)}")


def get_expenses_by_card(filtered_df: pd.DataFrame) -> list[dict]:
    """
    Функция принимает DataFrame с операциями и возвращает список словарей с суммарными расходами и суммарным
    кэшбэком по каждой карте
    :param filtered_df: DataFrame c операциями
    :return:
    """
    if filtered_df is None:
        raise ValueError("DataFrame is None")

        # Проверка существования столбца
    if "Номер карты" not in filtered_df.columns:
        raise ValueError("Столбец 'Номер карты' отсутствует в DataFrame")

    try:
        filtered_df["Номер карты"] = filtered_df["Номер карты"].str.replace(r"\D", "", regex=True)
        expenses_df = filtered_df[filtered_df["Сумма операции"] < 0]
        result_expenses = (
            expenses_df.groupby("Номер карты")
            .agg(total_expenses=("Сумма операции с округлением", "sum"), cashback=("Кэшбэк", "sum"))
            .reset_index()
        )
        result_expenses.columns = ["card_num", "total_expenses", "cashback"]
        try:
            result_expenses["total_expenses"] = result_expenses["total_expenses"].round(2)
        except:
            return result_expenses.to_dict(orient="records")
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
    required_columns = ["Дата платежа", "Сумма операции", "Сумма операции с округлением", "Категория", "Описание"]
    # Проверяем наличие всех обязательных столбцов
    missing_cols = [col for col in required_columns if col not in filtered_df.columns]
    if missing_cols:
        raise ValueError(f"Входной DataFrame не содержит необходимые столбцы: {missing_cols}")

    # Проверка корректности типов данных
    numeric_columns = ["Сумма операции", "Сумма операции с округлением"]
    # Пропустить проверку типов, если DataFrame пустой
    if not filtered_df.empty:
        for column in numeric_columns:
            if not pd.api.types.is_numeric_dtype(filtered_df[column]):
                raise TypeError(f"Содержимое столбца '{column}' должно быть числовым.")

    try:
        top_5 = filtered_df.sort_values(by="Сумма операции с округлением", ascending=True).head(5)
        columns = ["Дата платежа", "Сумма операции", "Категория", "Описание"]
        top_5_transactions = top_5[columns]
        top_5_transactions.columns = ["date", "amount", "category", "description"]
        return top_5_transactions.to_dict(orient="records")
    except Exception as ex:
        print(ex)
        return ex


def get_currency_rate() -> List[Dict]:
    """
    Функция возвращает список с курсами валют
    """
    url = "https://api.currencyapi.com/v3/latest"
    load_currency = load_user_settings()
    user_currency = load_currency.get("user_currencies")
    if not user_currency:
        return []
    result = []
    if not API_KEY_EXCHANGE:
        raise EnvironmentError("API_KEY_EXCHANGE environment variable is not set.")

    for currency in user_currency:
        try:
            params = {"apikey": API_KEY_EXCHANGE, "currencies": currency, "base_currency": "RUB"}
            resp = requests.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            rate = 1 / data.get("data", {}).get(currency, {}).get("value", 0)
            result.append({"currency": currency, "rate": round(rate, 2)})
        except requests.RequestException as req_err:
            print(f"Request error occurred: {req_err}")
            return []
        except Exception as err:
            print(f"An unexpected error occurred: {err}")
            return []
    return result


def get_stock_prices() -> List[Dict]:
    """
    Функция возвращает стоимость акций из списка в файле user_settings.json
    """

    user_stocks = load_user_settings()
    data = yf.Tickers(user_stocks["user_stocks"])
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


# print(get_first_day_of_month('2021-08-20 15:30:00'))
# print(load_user_settings())
# pprint(get_expenses_by_card(get_operation_for_period_from_excel()))
# get_top5_transaction(get_operation_for_period_from_excel())
# pprint(get_top5_transaction(get_operation_for_period_from_excel()))
# print(get_currency_rate())
# pprint(get_stock_prices())
# pprint(load_user_settings())
