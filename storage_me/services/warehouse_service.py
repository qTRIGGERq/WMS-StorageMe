"""
Сервисный слой бизнес-логики управления складом.
Реализует разделение ответственности (SRP) и инверсию зависимостей (DIP).
Сервис не выполняет прямой ввод/вывод в терминал, а выбрасывает доменные исключения.
"""

from typing import Any, Dict, List, Optional

from storage_me.exceptions import (
    DuplicateProductError,
    ProductNotFoundError,
    ValidationError,
)
from storage_me.models.movement import MovementType, StockMovement
from storage_me.models.product import Product
from storage_me.repositories.base import BaseWarehouseRepository


class WarehouseService:
    """
    Основной сервис бизнес-логики склада WMS.
    Управляет каталогом товаров, проводками движений и аудитом операций.
    """

    def __init__(self, repository: BaseWarehouseRepository, max_history_size: int = 200):
        self._repository: BaseWarehouseRepository = repository
        self._max_history_size: int = max_history_size
        self._products: Dict[str, Product] = {}
        self._stock_movements: List[StockMovement] = []
        self._reload()

    def _reload(self) -> None:
        """Перезагрузка данных из репозитория."""
        self._products, self._stock_movements = self._repository.load()

    @property
    def products(self) -> Dict[str, Product]:
        """Словарь всех товаров склада, индексированный по id."""
        return self._products

    @property
    def stock_movements(self) -> List[StockMovement]:
        """Полный список зафиксированных движений запасов."""
        return self._stock_movements

    # --- Операции создания и поиска товаров ---

    def create_product(self, name: str, quantity: int, price: float,
                       category: str = "Без категории",
                       location: str = "Не указано") -> Product:
        """
        Создает новый товар и фиксирует начальный остаток в истории движений.

        :raises DuplicateProductError: Если товар с таким наименованием уже существует.
        :raises ValidationError: При некорректных параметрах товара.
        """
        clean_name = str(name).strip()
        if not clean_name:
            raise ValidationError("Наименование товара не может быть пустым")

        for existing in self._products.values():
            if existing.name.lower() == clean_name.lower():
                raise DuplicateProductError(clean_name)

        product = Product(
            name=clean_name,
            quantity=quantity,
            price=price,
            category=category,
            location=location
        )

        self._products[product.id] = product

        # Формирование начального движения
        movement = StockMovement(
            movement_type=MovementType.ADD,
            product=product,
            quantity=product.quantity,
            reason="Первичное добавление товара на склад"
        )
        self._stock_movements.append(movement)

        self._trim_movements_history()
        self._repository.save(self._products, self._stock_movements)
        return product

    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Поиск товара по точному совпадению наименования (регистронезависимо)."""
        search = name.strip().lower()
        for product in self._products.values():
            if product.name.lower() == search:
                return product
        return None

    def get_product_by_id(self, product_id: str) -> Optional[Product]:
        """Поиск товара по уникальному ID."""
        return self._products.get(product_id.strip())

    def search_products_by_name(self, search_term: str) -> List[Product]:
        """Поиск товаров по подстроке наименования."""
        term = search_term.strip().lower()
        if not term:
            return []
        return [p for p in self._products.values() if term in p.name.lower()]

    def get_all_products(self) -> List[Product]:
        """Возвращает список всех товаров на складе."""
        return list(self._products.values())

    # --- Модификация товаров ---

    def update_product_quantity(self, product_name: str, new_quantity: int, reason: str = "") -> Product:
        """
        Изменение остатка товара на складе с фиксацией операции движения.

        :raises ProductNotFoundError: Если товар не найден.
        :raises ValidationError: Если количество недопустимо.
        """
        product = self.get_product_by_name(product_name)
        if not product:
            raise ProductNotFoundError(product_name)

        old_quantity = product.quantity
        diff = new_quantity - old_quantity

        if diff == 0:
            return product

        product.quantity = new_quantity
        m_type = MovementType.INCREASE if diff > 0 else MovementType.DECREASE
        clean_reason = reason.strip() or ("Поступление на склад" if diff > 0 else "Списание / отгрузка")

        movement = StockMovement(
            movement_type=m_type,
            product=product,
            quantity=abs(diff),
            reason=clean_reason
        )
        self._stock_movements.append(movement)

        self._trim_movements_history()
        self._repository.save(self._products, self._stock_movements)
        return product

    def update_product_info(self, product_name: str, **kwargs: Any) -> Product:
        """
        Обновление параметров товара (наименование, цена, категория, место хранения).

        :raises ProductNotFoundError: Если товар не найден.
        :raises DuplicateProductError: Если новое наименование занято другим товаром.
        """
        product = self.get_product_by_name(product_name)
        if not product:
            raise ProductNotFoundError(product_name)

        new_name = kwargs.get('name')
        if new_name is not None and new_name.strip():
            clean_new_name = new_name.strip()
            for other in self._products.values():
                if other.id != product.id and other.name.lower() == clean_new_name.lower():
                    raise DuplicateProductError(clean_new_name)
            product.name = clean_new_name

        if 'price' in kwargs and kwargs['price'] is not None:
            product.price = float(kwargs['price'])

        if 'category' in kwargs and kwargs['category'] is not None:
            product.category = str(kwargs['category'])

        if 'location' in kwargs and kwargs['location'] is not None:
            product.location = str(kwargs['location'])

        self._repository.save(self._products, self._stock_movements)
        return product

    def delete_product(self, product_name: str, reason: str = "Удаление товара со склада") -> Product:
        """
        Удаление товара со склада с регистрацией финального движения.

        :raises ProductNotFoundError: Если товар не найден.
        """
        product = self.get_product_by_name(product_name)
        if not product:
            raise ProductNotFoundError(product_name)

        movement = StockMovement(
            movement_type=MovementType.DELETE,
            product=product,
            quantity=product.quantity,
            reason=reason
        )
        self._stock_movements.append(movement)

        del self._products[product.id]

        self._trim_movements_history()
        self._repository.save(self._products, self._stock_movements)
        return product

    # --- Аналитика и выборки ---

    def get_products_by_category(self, category: Optional[str] = None) -> Dict[str, List[Product]]:
        """Группировка товаров по категориям или фильтрация по конкретной категории."""
        result: Dict[str, List[Product]] = {}
        target_cat = category.strip().lower() if category else None

        for p in self._products.values():
            if target_cat is None or p.category.lower() == target_cat:
                result.setdefault(p.category, []).append(p)
        return result

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        """Список товаров с количеством ниже порогового."""
        return [p for p in self._products.values() if p.is_low_stock(threshold)]

    def get_statistics(self) -> Dict[str, Any]:
        """Расчет агрегированной статистики по складу."""
        products = list(self._products.values())
        total_products = len(products)
        total_quantity = sum(p.quantity for p in products)
        total_value = sum(p.total_value() for p in products)

        most_expensive = max(products, key=lambda p: p.price) if products else None
        largest_quantity = max(products, key=lambda p: p.quantity) if products else None

        return {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'total_value': round(total_value, 2),
            'most_expensive': most_expensive,
            'largest_quantity': largest_quantity
        }

    def get_movements_history(self, limit: int = 20) -> List[StockMovement]:
        """Получение последних N записей аудита движения товаров."""
        if limit <= 0:
            return list(self._stock_movements)
        return self._stock_movements[-limit:]

    def _trim_movements_history(self) -> None:
        """Ограничение размера истории для предотвращения неограниченного роста в памяти."""
        if len(self._stock_movements) > self._max_history_size:
            self._stock_movements = self._stock_movements[-self._max_history_size:]
