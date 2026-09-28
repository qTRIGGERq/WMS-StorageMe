"""
Абстрактный интерфейс репозитория (Data Access Layer).
Демонстрирует принцип инверсии зависимостей (Dependency Inversion Principle, DIP из SOLID).
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from storage_me.models.movement import StockMovement
from storage_me.models.product import Product


class BaseWarehouseRepository(ABC):
    """
    Абстрактный базовый класс репозитория.
    Определяет контракт для любых источников данных (JSON, SQLite, PostgreSQL, память и т.д.).
    """

    @abstractmethod
    def load(self) -> Tuple[Dict[str, Product], List[StockMovement]]:
        """
        Загрузка всех товаров и истории перемещений из хранилища.

        :return: Кортеж из словаря товаров {id: Product} и списка движений [StockMovement].
        """
        raise NotImplementedError

    @abstractmethod
    def save(self, products: Dict[str, Product], movements: List[StockMovement]) -> None:
        """
        Сохранение товаров и истории перемещений в постоянное хранилище.

        :param products: Словарь товаров {id: Product}.
        :param movements: Список движений.
        """
        raise NotImplementedError
