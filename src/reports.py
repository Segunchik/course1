from datetime import datetime
from typing import Optional

import pandas as pd
from dateutil.relativedelta import relativedelta


def spending_by_category(transactions: pd.DataFrame, category: str, date: Optional[str] = None) -> pd.DataFrame:
    """
    Функция возвращает траты по заданной категории за последние три месяца от переданной даты.
    Если дата не передана, то берется текущая дата.
    :param transactions: дата фрейм с транзакциями
    :param category: категория
    :param date: заданная дата(опционально)
    :return:
    """
    if date is None:
        date_query = datetime.now()
    else:
        date_query = datetime.strptime(date, "%d.%m.%Y")
    date_3_months_ago = date_query - relativedelta(months=3)
    transactions["Дата операции"] = pd.to_datetime(transactions["Дата операции"], dayfirst=True)
    filtered_df = transactions[
        (transactions["Дата операции"] >= date_3_months_ago)
        & (transactions["Дата операции"] <= date_query)
        & (transactions["Категория"] == category)
    ]
    return filtered_df


# def read_excel():
#     return pd.read_excel("../data/operations.xlsx", sheet_name="Отчет по операциям")
#
# print(spending_by_category(read_excel(), "Фастфуд", "10.10.2020"))
