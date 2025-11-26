from datetime import datetime
from pprint import pprint

import pandas as pd
import pytest
from dateutil.relativedelta import relativedelta

from src.reports import spending_by_category


# Создадим тестовые данные
def create_test_transactions():
    data = {
        "Дата операции": [
            "01.11.2025",
            "15.10.2025",
            "20.09.2025",
            "05.09.2025",
            "10.08.2025",
            "25.07.2025",
            "01.01.2025",
        ],
        "Категория": ["Продукты", "Продукты", "Продукты", "Продукты", "Продукты", "Продукты", "Другое"],
        "Сумма": [1000, 2000, 1500, 3000, 800, 1200, 500],
    }
    return pd.DataFrame(data)


def test_spending_by_category_current_date():
    transactions = create_test_transactions()
    pprint(transactions)
    result = spending_by_category(transactions, "Продукты")
    print(result)
    # Проверяем, что все транзакции за последние 3 месяца по категории "Продукты"
    assert len(result) == 4  # Должно быть 4 транзакции за последние 3 месяца
    assert result["Категория"].unique() == ["Продукты"]
    assert result["Дата операции"].min() >= datetime.now() - relativedelta(months=3)


def test_spending_by_category_specific_date():
    transactions = create_test_transactions()
    result = spending_by_category(transactions, "Продукты", "30.10.2025")

    # Проверяем фильтрацию по указанной дате
    assert len(result) == 4  # Должно быть 4 транзакции за период
    assert result["Дата операции"].min() >= datetime(2025, 8, 1)
    assert result["Дата операции"].max() <= datetime(2025, 10, 30)


def test_spending_by_category_invalid_date_format():
    transactions = create_test_transactions()
    with pytest.raises(ValueError):
        spending_by_category(transactions, "Продукты", "2023-12-31")  # Неверный формат даты


def test_spending_by_category_empty_df():
    empty_df = pd.DataFrame(columns=["Дата операции", "Категория", "Сумма"])
    result = spending_by_category(empty_df, "Продукты")

    # Проверяем, что возвращается пустой DataFrame
    assert result.empty


def test_spending_by_category_no_matching_category():
    transactions = create_test_transactions()
    result = spending_by_category(transactions, "Несуществующая категория")

    # Проверяем, что возвращается пустой DataFrame
    assert result.empty


# Дополнительные проверки
def test_spending_by_category_date_range():
    transactions = create_test_transactions()
    start_date = datetime.now() - relativedelta(months=3)
    end_date = datetime.now()

    result = spending_by_category(transactions, "Продукты")

    # Проверяем диапазон дат
    assert result["Дата операции"].min() >= start_date
    assert result["Дата операции"].max() <= end_date
