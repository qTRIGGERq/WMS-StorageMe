"""
Реализация репозитория на основе JSON-файла.
"""

import json
import os
import tempfile
from typing import Dict, List, Tuple

from storage_me.exceptions import StorageError
from storage_me.models.movement import StockMovement
from storage_me.models.product import Product
from storage_me.repositories.base import BaseWarehouseRepository


class JsonWarehouseRepository(BaseWarehouseRepository):
    """
    Репозиторий, сохраняющий состояние склада в формате JSON.
    Обеспечивает атомарную запись и обработку ошибок дискового ввода-вывода.
    """

    def __init__(self, data_file: str = "warehouse_data.json"):
        self._data_file = data_file

    @property
    def data_file(self) -> str:
        return self._data_file

    def load(self) -> Tuple[Dict[str, Product], List[StockMovement]]:
        products: Dict[str, Product] = {}
        movements: List[StockMovement] = []

        if not os.path.exists(self._data_file) or os.path.getsize(self._data_file) == 0:
            return products, movements

        try:
            with open(self._data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            products_data = data.get('products', {})
            for pid, pdata in products_data.items():
                try:
                    product = Product.from_dict(pdata)
                    products[product.id] = product
                except Exception as e:
                    print(f"⚠️ Предупреждение: ошибка чтения товара с ID {pid}: {e}")

            movements_data = data.get('movements', [])
            for mdata in movements_data:
                try:
                    movement = StockMovement.from_dict(mdata, products)
                    movements.append(movement)
                except Exception as e:
                    print(f"⚠️ Предупреждение: ошибка чтения записи истории: {e}")

            return products, movements

        except (json.JSONDecodeError, OSError) as e:
            raise StorageError(f"Ошибка загрузки данных из файла '{self._data_file}': {e}") from e

    def save(self, products: Dict[str, Product], movements: List[StockMovement]) -> None:
        data = {
            'products': {pid: prod.to_dict() for pid, prod in products.items()},
            'movements': [m.to_dict() for m in movements]
        }

        # Атомарная запись через временный файл в той же директории
        dir_name = os.path.dirname(os.path.abspath(self._data_file)) or "."
        try:
            with tempfile.NamedTemporaryFile('w', dir=dir_name, delete=False, encoding='utf-8') as tf:
                json.dump(data, tf, ensure_ascii=False, indent=2)
                temp_name = tf.name

            # Атомарная замена файла
            os.replace(temp_name, self._data_file)
        except OSError as e:
            if 'temp_name' in locals() and os.path.exists(temp_name):
                try:
                    os.remove(temp_name)
                except OSError:
                    pass
            raise StorageError(f"Ошибка сохранения данных в файл '{self._data_file}': {e}") from e
