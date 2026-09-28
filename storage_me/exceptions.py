"""
Иерархия доменных исключений WMS-StorageMe.
Демонстрирует принципы ООП: наследование исключений и обработку ошибок предметной области.
"""


class WMSException(Exception):
    """Базовое исключение для всех ошибок складской системы."""
    pass


class EntityNotFoundError(WMSException):
    """Сущность не найдена в хранилище."""
    pass


class ProductNotFoundError(EntityNotFoundError):
    """Товар с указанным именем или идентификатором не найден."""
    def __init__(self, product_identifier: str):
        super().__init__(f"Товар '{product_identifier}' не найден!")
        self.product_identifier = product_identifier


class DuplicateProductError(WMSException):
    """Попытка создания или переименования товара с уже существующим наименованием."""
    def __init__(self, product_name: str):
        super().__init__(f"Товар с наименованием '{product_name}' уже существует!")
        self.product_name = product_name


class ValidationError(WMSException):
    """Ошибка валидации данных сущности."""
    pass


class InvalidQuantityError(ValidationError):
    """Количество товара имеет недопустимое значение."""
    pass


class InvalidPriceError(ValidationError):
    """Цена товара имеет недопустимое значение."""
    pass


class StorageError(WMSException):
    """Ошибка сохранения или загрузки данных из репозитория."""
    pass
