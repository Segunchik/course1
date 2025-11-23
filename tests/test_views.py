import unittest
from pprint import pprint
from unittest.mock import patch, MagicMock
import json
from datetime import datetime

from src.views import main_info


# from views import main_info
TEST_DATETIME = "2021-08-20 15:30:00"

def test_main_info():
    # Создаем тестовые данные
   # test_datetime = "2021-08-20 15:30:00"
    mock_cards = [
        {'card_num': '4556', 'total_expenses': 3361.7, 'cashback': 154.0},
        {'card_num': '7197', 'total_expenses': 6959.48, 'cashback': 0.0}
    ]
    mock_top_transactions = [
        {"amount": 1000, "description": "Transaction 1"},
        {"amount": 500, "description": "Transaction 2"}
    ]
    mock_currency_rates = {"USD": 75.0, "EUR": 85.0}
    mock_stock_prices = {"AAPL": 150.0, "GOOGL": 2500.0}
    mock_greeting = "Добрый день"

    with patch('src.views.get_operation_for_period_from_excel') as mock_excel:
        with patch('src.views.greeting_by_time_of_day') as mock_greeting_func:
            with patch('src.views.get_expenses_by_card') as mock_cards_func:
                with patch('src.views.get_top5_transaction') as mock_top:
                    with patch('src.views.get_currency_rate') as mock_currency:
                        with patch('src.views.get_stock_prices') as mock_stock:
                            # Настраиваем моки
                            mock_excel.return_value = MagicMock()
                            print(f'mock_excel:{mock_excel}')
                            mock_greeting_func.return_value = mock_greeting
                            mock_cards_func.return_value = mock_cards
                            mock_top.return_value = mock_top_transactions
                            mock_currency.return_value = mock_currency_rates
                            mock_stock.return_value = mock_stock_prices

                            # Вызываем тестируемую функцию
                            result = main_info(TEST_DATETIME)
                            pprint(result)
                            # Проверяем результат
                            data = json.loads(result)
                            assert data['greeting'] == mock_greeting
                            assert data['cards'] == mock_cards
                            assert data['top_transactions'] == mock_top_transactions
                            assert data['currency_rates'] == mock_currency_rates
                            assert data['stock_prices'] == mock_stock_prices
