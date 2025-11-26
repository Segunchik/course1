import pytest

from src.services import simple_search

transactions = [
    {"id": 1, "category": "Продукты", "description": "Покупка в супермаркете", "amount": 1500},
    {"id": 2, "category": "Транспорт", "description": "Поездка на такси", "amount": 300},
    {"id": 3, "category": "Развлечения", "description": "Билет в кино", "amount": 500},
    {"id": 4, "category": "Хобби", "description": "Книги", "amount": 800},
]


def test_simple_search_empty_query():
    with pytest.raises(ValueError):
        simple_search("", transactions)


def test_simple_search_whitespace_query():
    with pytest.raises(ValueError):
        simple_search("   ", transactions)


def test_simple_search_category_match():
    result = simple_search("продукты", transactions)
    assert len(result) == 1
    assert result[0]["id"] == 1


def test_simple_search_description_match():
    result = simple_search("такси", transactions)
    assert len(result) == 1
    assert result[0]["id"] == 2


def test_simple_search_multiple_matches():
    result = simple_search("в", transactions)
    assert len(result) == 2
