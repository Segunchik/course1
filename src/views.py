import json
from pprint import pprint

from src.utils import get_operation_for_period_from_excel, greeting_by_time_of_day, get_expenses_by_card, \
    get_top5_transaction, get_currency_rate, get_stock_prices


def main_info(date_time: str) -> str:
    """
    Функция, принимающая на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS и возвращающую JSON-ответ
    :param date_time: 2021-08-20 15:30:00
    :return:
    """

    sorted_df = get_operation_for_period_from_excel("data/operations.xlsx", date_time)
    greeting = greeting_by_time_of_day()
    cards = get_expenses_by_card(sorted_df)
    top_transactions = get_top5_transaction(sorted_df)
    currency_rates = get_currency_rate()
    stock_prices = get_stock_prices()

    data = {
        "greeting": greeting,
        "cards": cards,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices
    }
    json_data = json.dumps(data, ensure_ascii=False, indent=4)
    return json_data