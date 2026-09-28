"""
Модель товара на складе.
Демонстрирует инкапсуляцию, валидацию данных через @property и наследование от BaseEntity.
"""

from datetime import datetime
from typing import Any, Dict

from storage_me.exceptions import InvalidPriceError, InvalidQuantityError, ValidationError
from storage_me.models.base import BaseEntity


class Product(BaseEntity):
    """
    Сущность складского товара.
    Хранит атрибуты товара, обеспечивает валидацию данных и расчет суммарной стоимости.
    """

    def __init__(self,
                 name: str,
                 quantity: int,
                 price: float,
                 category: str = "Без категории",
                 location: str = "Не указано",
                 product_id: str | None = None,
                 created_at: datetime | None = None,
                 updated_at: datetime | None = None):
        super().__init__(entity_id=product_id, created_at=created_at, updated_at=updated_at)
        self._name: str = ""
        self._quantity: int = 0
        self._price: float = 0.0
        self._category: str = ""
        self._location: str = ""

        # Валидация через сеттеры
        self.name = name
        self.quantity = quantity
        self.price = price
        self.category = category
        self.location = location

    # --- Геттеры и сеттеры (Инкапсуляция и валидация) ---

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        if not value or not str(value).strip():
            raise ValidationError("Наименование товара не может быть пустым")
        self._name = str(value).strip()
        self.touch()

    @property
    def quantity(self) -> int:
        return self._quantity

    @quantity.setter
    def quantity(self, value: int) -> None:
        try:
            val_int = int(value)
        except (ValueError, TypeError):
            raise InvalidQuantityError(f"Недопустимое значение количества: {value}")
        if val_int < 0:
            raise InvalidQuantityError("Количество товара не может быть отрицательным")
        self._quantity = val_int
        self.touch()

    @property
    def price(self) -> float:
        return self._price

    @price.setter
    def price(self, value: float) -> None:
        try:
            val_float = float(value)
        except (ValueError, TypeError):
            raise InvalidPriceError(f"Недопустимое значение цены: {value}")
        if val_float < 0:
            raise InvalidPriceError("Цена товара не может быть отрицательной")
        self._price = round(val_float, 2)
        self.touch()

    @property
    def category(self) -> str:
        return self._category

    @category.setter
    def category(self, value: str) -> None:
        cleaned = str(value).strip() if value else "Без категории"
        self._category = cleaned or "Без категории"
        self.touch()

    @property
    def location(self) -> str:
        return self._location

    @location.setter
    def location(self, value: str) -> None:
        cleaned = str(value).strip() if value else "Не указано"
        self._location = cleaned or "Не указано"
        self.touch()

    # --- Бизнес-методы сущности ---

    def total_value(self) -> float:
        """Расчет общей стоимости товарной позиции на складе."""
        return round(self._quantity * self._price, 2)

    def is_low_stock(self, threshold: int = 10) -> bool:
        """Проверка, является ли остаток товара критически низким."""
        return self._quantity < threshold

    # --- Сериализация и десериализация ---

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self._id,
            'name': self._name,
            'quantity': self._quantity,
            'price': self._price,
            'category': self._category,
            'location': self._location,
            'created_at': self._created_at.isoformat(),
            'updated_at': self._updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Product':
        created_at = datetime.fromisoformat(data['created_at']) if 'created_at' in data else None
        updated_at = datetime.fromisoformat(data['updated_at']) if 'updated_at' in data else None
        return cls(
            name=data['name'],
            quantity=int(data['quantity']),
            price=float(data['price']),
            category=data.get('category', 'Без категории'),
            location=data.get('location', 'Не указано'),
            product_id=data.get('id'),
            created_at=created_at,
            updated_at=updated_at
        )

    def __str__(self) -> str:
        return (f"{self._name} [ID: {self._id}] — "
                f"{self._quantity} шт. × {self._price:.2f} ₽ = {self.total_value():.2f} ₽ "
                f"(Категория: {self._category}, Место: {self._location})")
