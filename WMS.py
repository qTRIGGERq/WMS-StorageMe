#!/usr/bin/env python3
"""
WMS-StorageMe: Модуль обратной совместимости.
Предоставляет точку входа и псевдонимы для обратной совместимости со старой монолитной версией.
Основная модульная архитектура проекта расположена в пакете `storage_me/`.
"""

import os
import sys

# Обеспечиваем доступность пакета storage_me
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_me.exceptions import (
    DuplicateProductError,
    InvalidPriceError,
    InvalidQuantityError,
    ProductNotFoundError,
    StorageError,
    ValidationError,
    WMSException,
)
from storage_me.models.base import BaseEntity
from storage_me.models.movement import MovementType, StockMovement
from storage_me.models.product import Product
from storage_me.repositories.base import BaseWarehouseRepository
from storage_me.repositories.json_repository import JsonWarehouseRepository
from storage_me.services.warehouse_service import WarehouseService
from storage_me.ui.console_app import WarehouseApp

# Псевдоним репозитория для совместимости со старыми тестами/скриптами
WarehouseRepository = JsonWarehouseRepository


def main():
    app = WarehouseApp()
    app.run()


if __name__ == "__main__":
    main()
