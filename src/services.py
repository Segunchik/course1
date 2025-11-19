from typing import Any, Dict, List


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Функция ищет транзакции по указанным полям
    """
    if not query.strip():
        raise ValueError("Запрос не может быть пустым")

    query_lower = query.lower()

    return [
        transaction
        for transaction in transactions
        if query_lower in str(transaction.get("category", "")).lower()
        or query_lower in str(transaction.get("description", "")).lower()
    ]
