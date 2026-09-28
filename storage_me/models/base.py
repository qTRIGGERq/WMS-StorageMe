"""
Базовый класс для доменных сущностей (Entity).
Демонстрирует принципы ООП: Абстракцию (ABC), Инкапсуляцию и Наследование.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict
import uuid


class BaseEntity(ABC):
    """
    Абстрактный базовый класс для всех сущностей системы.
    Определяет единый идентификатор, временные метки создания/модификации,
    а также обязательный интерфейс сериализации в словарь.
    """

    def __init__(self, entity_id: str | None = None,
                 created_at: datetime | None = None,
                 updated_at: datetime | None = None):
        self._id: str = entity_id or str(uuid.uuid4())[:8]
        now = datetime.now()
        self._created_at: datetime = created_at or now
        self._updated_at: datetime = updated_at or now

    @property
    def id(self) -> str:
        """Уникальный строковый идентификатор сущности."""
        return self._id

    @property
    def created_at(self) -> datetime:
        """Дата и время создания сущности."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Дата и время последнего обновления сущности."""
        return self._updated_at

    def touch(self) -> None:
        """Обновляет отметку времени последнего изменения."""
        self._updated_at = datetime.now()

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Сериализация сущности в словарь для персистентного хранения."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self._id}>"
