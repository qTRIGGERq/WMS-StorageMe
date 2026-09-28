"""
Модель движения (транзакции) товара на складе.
Фиксирует приход, расход, списание и удаление позиций с указанием причины.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict

from storage_me.exceptions import ValidationError
from storage_me.models.base import BaseEntity
from storage_me.models.product import Product


class MovementType(str, Enum):
    """Типы складских операций."""
    ADD = "ADD"            # Первичное добавление товара
    INCREASE = "INCREASE"  # Поступление / приход
    DECREASE = "DECREASE"  # Отгрузка / списание
    DELETE = "DELETE"      # Удаление товара со склада

    @property
    def symbol(self) -> str:
        symbols = {
            MovementType.ADD: "➕",
            MovementType.INCREASE: "⬆️",
            MovementType.DECREASE: "⬇️",
            MovementType.DELETE: "🗑️"
        }
        return symbols.get(self, "➡️")

    @property
    def description(self) -> str:
        descs = {
            MovementType.ADD: "Создание товара",
            MovementType.INCREASE: "Поступление товара",
            MovementType.DECREASE: "Отгрузка/списание",
            MovementType.DELETE: "Удаление товара"
        }
        return descs.get(self, "Операция")


class StockMovement(BaseEntity):
    """
    Сущность движения запасов.
    Обеспечивает неизменяемость аудиторского следа складских операций.
    """

    def __init__(self,
                 movement_type: MovementType | str,
                 product: Product | None,
                 quantity: int,
                 reason: str,
                 product_id: str | None = None,
                 product_name: str | None = None,
                 movement_id: str | None = None,
                 timestamp: datetime | None = None):
        super().__init__(entity_id=movement_id, created_at=timestamp, updated_at=timestamp)

        # Тип движения
        if isinstance(movement_type, MovementType):
            self._type = movement_type
        else:
            try:
                self._type = MovementType(str(movement_type).upper())
            except ValueError:
                raise ValidationError(f"Неизвестный тип движения: {movement_type}")

        # Товар и его метаданные
        self._product = product
        self._product_id = product.id if product else (product_id or "")
        self._product_name = product.name if product else (product_name or "Неизвестно")

        if quantity < 0:
            raise ValidationError("Количество в операции движения не может быть отрицательным")
        self._quantity = int(quantity)
        self._reason = str(reason).strip() or "Без указания причины"

    @property
    def timestamp(self) -> datetime:
        return self._created_at

    @property
    def type(self) -> MovementType:
        return self._type

    @property
    def product(self) -> Product | None:
        return self._product

    @property
    def product_id(self) -> str:
        return self._product_id

    @property
    def product_name(self) -> str:
        return self._product_name

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def reason(self) -> str:
        return self._reason

    def get_type_symbol(self) -> str:
        return self._type.symbol

    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'type': self._type.value,
            'product_id': self._product_id,
            'product_name': self._product_name,
            'quantity': self._quantity,
            'reason': self._reason
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], products: Dict[str, Product] | None = None) -> 'StockMovement':
        product_id = data.get('product_id', '')
        product = products.get(product_id) if products else None
        timestamp = datetime.fromisoformat(data['timestamp']) if 'timestamp' in data else None

        return cls(
            movement_type=data.get('type', 'ADD'),
            product=product,
            quantity=int(data.get('quantity', 0)),
            reason=data.get('reason', ''),
            product_id=product_id,
            product_name=data.get('product_name', product.name if product else 'Неизвестно'),
            timestamp=timestamp
        )

    def __str__(self) -> str:
        return (f"{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} {self._type.symbol} "
                f"[{self._type.value}] {self._product_name} (ID: {self._product_id}): "
                f"{self._quantity} шт. | Причина: {self._reason}")
