import json
import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

import openpyxl
from pathlib import Path

import pandas as pd
import pytest
from freezegun import freeze_time

from src.utils import greeting_by_time_of_day, get_first_day_of_month, load_user_settings, \
    get_operation_for_period_from_excel, get_expenses_by_card, get_top5_transaction, get_currency_rate, get_stock_prices


def test_greeting_morning():
    with freeze_time("2025-11-08 07:00:00"):
        assert greeting_by_time_of_day() == "Доброе утро"


def test_greeting_day():
    with freeze_time("2025-11-08 13:00:00"):
        assert greeting_by_time_of_day() == "Добрый день"


def test_greeting_evening():
    with freeze_time("2025-11-08 19:00:00"):
        assert greeting_by_time_of_day() == "Добрый вечер"


def test_greeting_night():
    with freeze_time("2025-11-08 01:00:00"):
        assert greeting_by_time_of_day() == "Доброй ночи"


def test_get_first_day_of_month():
    # Тест с обычной датой
    input_date = "15.03.2023 14:30:00"
    expected_output = "01.03.2023 00:00:00"
    assert get_first_day_of_month(input_date) == expected_output


def test_first_day():
    # Тест с первым числом месяца
    input_date = "01.05.2023 00:00:00"
    expected_output = "01.05.2023 00:00:00"
    assert get_first_day_of_month(input_date) == expected_output


def test_last_day():
    # Тест с последним числом месяца
    input_date = "31.12.2023 23:59:59"
    expected_output = "01.12.2023 00:00:00"
    assert get_first_day_of_month(input_date) == expected_output


def test_load_user_settings():
    # Создаем временный файл для тестирования
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as temp_file:
        # Записываем тестовые данные
        test_data = {
            "user_currencies": ["USD", "EUR", "GBP"],
            "user_stocks": ["AAPL", "GOOG", "TSLA", "AMZN"]
        }

        # Записываем данные в файл
        json.dump(test_data, temp_file)
        temp_file.flush()  # Очищаем буфер
        temp_file.seek(0)  # Переводим указатель в начало файла

        temp_file_path = Path(temp_file.name)

        # Тест с существующим файлом
        result = load_user_settings(temp_file_path)
        assert result == test_data, f"Ошибка при чтении существующего файла. Ожидалось: {test_data}, получено: {result}"


def test_non_exist_file():
    # Тест с несуществующим файлом
    non_existent_file = Path("non_existent_file.json")
    result = load_user_settings(non_existent_file)
    assert result == {}, "Ошибка при обработке несуществующего файла"


def test_empty_file():
    # Тест с пустым файлом
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as empty_file:
        empty_file.write('{}')
        empty_file.flush()
        empty_file.seek(0)
        empty_file_path = Path(empty_file.name)
        result = load_user_settings(empty_file_path)
        assert result == {}, "Ошибка при чтении пустого файла"


def test_incorrect_json():
    # Тест с некорректным JSON
    with tempfile.NamedTemporaryFile(delete=False, mode='w+', encoding='utf-8') as invalid_file:
        invalid_file.write("{invalid json")
        invalid_file.flush()
        invalid_file.seek(0)
        invalid_file_path = Path(invalid_file.name)
        try:
            load_user_settings(invalid_file_path)
            assert False, "Функция не сгенерировала исключение при некорректном JSON"
        except json.JSONDecodeError:
            pass


def create_test_excel():
    test_file_path = 'test_operations.xlsx'
    data = {
        'Дата операции': ['01.10.2021 08:00:00', '05.10.2021 12:00:00', '10.10.2021 10:10:10', '15.10.2021 14:00:00'],
        'Сумма': [100, 200, 300, 400],
    }
    df = pd.DataFrame(data)
    df.to_excel(test_file_path, index=False, sheet_name='Отчет по операциям')
    return test_file_path


def remove_test_excel(path):
    Path(path).unlink(missing_ok=True)


def test_get_operation_for_period_from_excel_valid_data_and_dates():
    test_file_path = create_test_excel()
    expected_result = pd.DataFrame({
        'Дата операции': ["2021-10-01T08:00:00", "2021-10-05T12:00:00", "2021-10-10T10:10:10"],
        'Сумма': [100, 200, 300]
    })
    actual_result = get_operation_for_period_from_excel(test_file_path, "10.10.2021 10:10:10")
    actual_result['Дата операции'] = actual_result['Дата операции'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    pd.testing.assert_frame_equal(actual_result.reset_index(drop=True), expected_result.reset_index(drop=True))
    remove_test_excel(test_file_path)


def test_get_operation_for_period_from_excel_invalid_file_path():
    with patch.object(Path, 'exists') as mock_exists:
        mock_exists.return_value = False
        result = get_operation_for_period_from_excel('nonexistent_file.xlsx', "10.10.2021 10:10:10")
        assert result is None


def test_get_operation_for_period_from_excel_invalid_date_format():
    with unittest.TestCase().assertRaises(ValueError):
        get_operation_for_period_from_excel(create_test_excel(), "invalid-date-format")


@pytest.fixture
def sample_filtered_df():
    data = {
        'Номер карты': ['1234567890123456', '2345678901234567', '1234567890123456'],
        'Сумма операции': [-100, -200, -50],  # Отрицательные суммы означают расходы
        'Сумма операции с округлением': [-100, -200, -50],
        'Кэшбэк': [10, 20, 5]
    }
    return pd.DataFrame(data)


def test_get_expenses_by_card(sample_filtered_df):
    # Основная проверка работоспособности функции
    result = get_expenses_by_card(sample_filtered_df)
    expected_output = [
        {'card_num': '1234567890123456', 'total_expenses': -150, 'cashback': 15},
        {'card_num': '2345678901234567', 'total_expenses': -200, 'cashback': 20}
    ]
    assert len(result) == len(expected_output)
    for res, exp in zip(result, expected_output):
        assert res['card_num'] == exp['card_num'], f'Карточный номер не совпадает'
        assert res['total_expenses'] == exp['total_expenses'], f'Расходы не совпадают'
        assert res['cashback'] == exp['cashback'], f'Кэшбэк не совпадает'


def test_empty_input():
    empty_df = pd.DataFrame(columns=['Номер карты', 'Сумма операции', 'Сумма операции с округлением', 'Кэшбэк'])
    result = get_expenses_by_card(empty_df)
    assert isinstance(result, list)
    assert len(result) == 0


def test_missing_columns():
    missing_column_df = pd.DataFrame({
        'Номер карты': [],
        'Сумма операции': [],
        'Кэшбэк': []
    }).astype({'Номер карты': 'str'})
    with pytest.raises(KeyError):  # Так как отсутствует обязательный столбец 'Сумма операции с округлением'
        get_expenses_by_card(missing_column_df)


def test_all_nonnegative_amounts():
    nonneg_df = pd.DataFrame({
        'Номер карты': ['1234567890123456', '2345678901234567'],
        'Сумма операции': [100, 200],
        'Сумма операции с округлением': [100, 200],
        'Кэшбэк': [10, 20]
    })
    result = get_expenses_by_card(nonneg_df)
    assert len(result) == 0  # Все положительные суммы игнорируются как расходы

@pytest.fixture
def sample_filtered_df_for_top5():
    data = {
        'Дата платежа': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05', '2023-01-06'],
        'Сумма операции': [-100, -200, -300, -400, -500, -600],
        'Сумма операции с округлением': [-100, -200, -300, -400, -500, -600],
        'Категория': ['Еда', 'Транспорт', 'Развлечения', 'Здоровье', 'Путешествия', 'Интернет'],
        'Описание': ['Покупка продуктов', 'Проезд на автобусе', 'Посещение кинотеатра', 'Лечение зубов', 'Поездка в Сочи', 'Оплата хостинга']
    }
    return pd.DataFrame(data)

def test_get_top5_transaction_correct_functionality(sample_filtered_df_for_top5):
    # Проверка нормальной работы функции
    result = get_top5_transaction(sample_filtered_df_for_top5)
    expected_output = [
        {"date": "2023-01-06", "amount": -600, "category": "Интернет", "description": "Оплата хостинга"},
        {"date": "2023-01-05", "amount": -500, "category": "Путешествия", "description": "Поездка в Сочи"},
        {"date": "2023-01-04", "amount": -400, "category": "Здоровье", "description": "Лечение зубов"},
        {"date": "2023-01-03", "amount": -300, "category": "Развлечения", "description": "Посещение кинотеатра"},
        {"date": "2023-01-02", "amount": -200, "category": "Транспорт", "description": "Проезд на автобусе"}
    ]
    assert result == expected_output

def test_get_top5_transaction_empty_dataframe():
    # Проверка на пустой DataFrame
    empty_df = pd.DataFrame(columns=["Дата платежа", "Сумма операции", "Сумма операции с округлением", "Категория", "Описание"])
    result = get_top5_transaction(empty_df)
    assert result == []

def test_get_top5_transaction_few_records():
    # Проверка на недостаточное количество записей (<5)
    few_records_df = pd.DataFrame({
        'Дата платежа': ['2023-01-01', '2023-01-02'],
        'Сумма операции': [-100, -200],
        'Сумма операции с округлением': [-100, -200],
        'Категория': ['Еда', 'Транспорт'],
        'Описание': ['Покупка продуктов', 'Проезд на автобусе']
    })
    result = get_top5_transaction(few_records_df)
    expected_output = [
        {"date": "2023-01-02", "amount": -200, "category": "Транспорт", "description": "Проезд на автобусе"},
        {"date": "2023-01-01", "amount": -100, "category": "Еда", "description": "Покупка продуктов"}
    ]
    assert result == expected_output

def test_get_top5_transaction_missing_columns():
    # Проверка на отсутствие обязательных столбцов
    missing_column_df = pd.DataFrame({
        'Дата платежа': ['2023-01-01', '2023-01-02'],
        'Сумма операции': [-100, -200],
        'Категория': ['Еда', 'Транспорт'],
        'Описание': ['Покупка продуктов', 'Проезд на автобусе']
    })  # Нет столбца "Сумма операции с округлением"
    with pytest.raises(Exception):
        get_top5_transaction(missing_column_df)

def test_get_top5_transaction_exception_handling():
    # Проверка обработки исключительной ситуации
    incorrect_type_df = pd.DataFrame({
        'Дата платежа': ['2023-01-01', '2023-01-02'],
        'Сумма операции': [-100, '-200'],  # Некорректный тип данных
        'Сумма операции с округлением': [-100, '-200'],
        'Категория': ['Еда', 'Транспорт'],
        'Описание': ['Покупка продуктов', 'Проезд на автобусе']
    })
    with pytest.raises(Exception):
        get_top5_transaction(incorrect_type_df)


MOCK_USER_SETTINGS = {"user_currencies": ["USD", "EUR"]}

# Валидная информация о курсах валют
VALID_RESPONSE_DATA = {
    "data": {
        "USD": {"code": "USD", "value": 1/73.54},
        "EUR": {"code": "EUR", "value": 1/85.21},
    }
}

# Неверный ответ (при ошибке API)
INVALID_RESPONSE_DATA = {}

@pytest.fixture
def mock_load_user_settings(monkeypatch):
    with patch("src.utils.load_user_settings", return_value=MOCK_USER_SETTINGS) as mock:
        yield mock
        assert mock.call_count > 0

   # monkeypatch.setattr("src.utils.load_user_settings", lambda: MOCK_USER_SETTINGS)
    # monkeypatch.setattr(load_user_settings, "__func__", lambda: MOCK_USER_SETTINGS)
    #assert load_user_settings() == MOCK_USER_SETTINGS

@patch("requests.get")
@patch("src.utils.load_user_settings")
def test_get_currency_rate_success(mock_load_user_settings, mock_requests_get):#, mock_load_user_settings):
    # Эмулируем успешный ответ от API
    mock_load_user_settings.return_value = MOCK_USER_SETTINGS
    print("load_user_settings", )
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = VALID_RESPONSE_DATA

    print("Загруженные настройки:", mock_load_user_settings.return_value)
    print("Ответ API:", mock_requests_get.return_value.json.return_value)

    assert mock_load_user_settings.return_value == MOCK_USER_SETTINGS
    assert mock_requests_get.return_value.status_code == 200

    result = get_currency_rate()
    print("Результат функции:", result)
    expected_result = [
        {"currency": "USD", "rate": 73.54},
        {"currency": "EUR", "rate": 85.21}
    ]
#    assert load_user_settings() == MOCK_USER_SETTINGS
    assert result == expected_result

@patch("requests.get")
def test_get_currency_rate_invalid_response(mock_requests_get, mock_load_user_settings):
    # Эмулируем ошибку API (ответ без полезных данных)
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = INVALID_RESPONSE_DATA

    result = get_currency_rate()
    assert result == []

@patch("requests.get")
def test_get_currency_rate_api_error(mock_requests_get, mock_load_user_settings):
    # Эмулируем ошибку API (например, статус 401)
    mock_requests_get.return_value.status_code = 401
    mock_requests_get.return_value.json.side_effect = Exception("API Error")

    result = get_currency_rate()
    assert result == []

@patch("requests.get")
def test_get_currency_rate_network_error(mock_requests_get, mock_load_user_settings):
    # Эмулируем сетевую ошибку
    mock_requests_get.side_effect = ConnectionError("Network failure")

    result = get_currency_rate()
    assert result == []


MOCK_USER_SETTINGS_STOCKS = {
   "user_stocks": ["AAPL", "GOOGL", "MSFT"]
}

MOCK_STOCK_DATA = {
    "AAPL": {"currentPrice": 150.75},
    "GOOGL": {"currentPrice": 2800.50},
    "MSFT": {"currentPrice": 325.25}
}


@pytest.fixture
def mock_load_user_settings(monkeypatch):
    def mock_function():
        return MOCK_USER_SETTINGS_STOCKS

    monkeypatch.setattr("src.utils.load_user_settings", mock_function)


@pytest.fixture
def mock_yf_tickers():
    with patch("src.utils.yf.Tickers") as mock_tickers:
        # Создаем моковые данные для каждой акции
        mock_tickers_dict = {
            symbol: MagicMock(info=MOCK_STOCK_DATA[symbol])
            for symbol in MOCK_USER_SETTINGS_STOCKS["user_stocks"]
        }

        # Настраиваем поведение mock_tickers
        mock_tickers.return_value = MagicMock(
            tickers=mock_tickers_dict
        )
        yield mock_tickers


def test_get_stock_prices_success(mock_load_user_settings, mock_yf_tickers):
    result = get_stock_prices()

    expected_result = [
        {"stock": "AAPL", "price": 150.75},
        {"stock": "GOOGL", "price": 2800.50},
        {"stock": "MSFT", "price": 325.25}
    ]

    assert result == expected_result
    assert len(result) == 3
    for item in result:
        assert isinstance(item["price"], float)
        assert round(item["price"], 2) == item["price"]


def test_get_stock_prices_missing_data(mock_load_user_settings, mock_yf_tickers):
    # Добавляем акцию без данных
    MOCK_USER_SETTINGS_STOCKS["user_stocks"].append("NONEXISTENT")

    # Мокаем отсутствие данных для несуществующей акции
    mock_yf_tickers.return_value.tickers["NONEXISTENT"] = MagicMock(info={})

    result = get_stock_prices()

    expected_result = [
        {"stock": "AAPL", "price": 150.75},
        {"stock": "GOOGL", "price": 2800.50},
        {"stock": "MSFT", "price": 325.25}
    ]

    assert result == expected_result
    assert len(result) == 3


