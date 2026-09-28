"""
Модульные тесты сервисного слоя (WarehouseService).
"""

import os
import tempfile
import unittest

from storage_me.exceptions import DuplicateProductError, ProductNotFoundError
from storage_me.repositories.json_repository import JsonWarehouseRepository
from storage_me.services.warehouse_service import WarehouseService


class TestWarehouseService(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.repo = JsonWarehouseRepository(data_file=self.temp_file.name)
        self.service = WarehouseService(self.repo)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_create_product(self):
        prod = self.service.create_product("Серверная стойка", 2, 45000.0, "Оборудование", "Зал 1")
        self.assertEqual(prod.name, "Серверная стойка")
        self.assertEqual(len(self.service.get_all_products()), 1)
        self.assertEqual(len(self.service.stock_movements), 1)

    def test_duplicate_product_rejected(self):
        self.service.create_product("Планшет", 5, 20000.0)
        with self.assertRaises(DuplicateProductError):
            self.service.create_product("планшет", 3, 22000.0)

    def test_update_quantity_creates_movement(self):
        self.service.create_product("Коммутатор", 10, 8000.0)
        self.service.update_product_quantity("Коммутатор", 15, "Поставка новой партии")

        prod = self.service.get_product_by_name("Коммутатор")
        self.assertEqual(prod.quantity, 15)
        # 1-е движение ADD, 2-е INCREASE
        self.assertEqual(len(self.service.stock_movements), 2)
        last_mov = self.service.stock_movements[-1]
        self.assertEqual(last_mov.quantity, 5)
        self.assertEqual(last_mov.type.value, "INCREASE")

    def test_search_products(self):
        self.service.create_product("Кабель питания 1.8м", 50, 150.0)
        self.service.create_product("Кабель HDMI 2.0", 30, 450.0)
        self.service.create_product("Мышь проводная", 10, 500.0)

        results = self.service.search_products_by_name("кабель")
        self.assertEqual(len(results), 2)

    def test_statistics(self):
        self.service.create_product("Товар А", 10, 100.0)  # 1000
        self.service.create_product("Товар Б", 5, 200.0)   # 1000

        stats = self.service.get_statistics()
        self.assertEqual(stats['total_products'], 2)
        self.assertEqual(stats['total_quantity'], 15)
        self.assertEqual(stats['total_value'], 2000.0)
        self.assertEqual(stats['most_expensive'].name, "Товар Б")
        self.assertEqual(stats['largest_quantity'].name, "Товар А")

    def test_delete_product(self):
        self.service.create_product("Временный товар", 5, 100.0)
        self.service.delete_product("Временный товар", reason="Списание брака")

        self.assertIsNone(self.service.get_product_by_name("Временный товар"))
        self.assertEqual(len(self.service.get_all_products()), 0)
        last_mov = self.service.stock_movements[-1]
        self.assertEqual(last_mov.type.value, "DELETE")

    def test_delete_nonexistent_product_raises_error(self):
        with self.assertRaises(ProductNotFoundError):
            self.service.delete_product("Несуществующий товар")

    def test_update_quantity_nonexistent_product(self):
        with self.assertRaises(ProductNotFoundError):
            self.service.update_product_quantity("Несуществующий товар", 10)

    def test_filter_by_category(self):
        self.service.create_product("Роутер", 10, 3000.0, category="Сеть")
        self.service.create_product("Свитч", 5, 5000.0, category="Сеть")
        self.service.create_product("Монитор", 2, 20000.0, category="Периферия")

        network_items = self.service.get_products_by_category("Сеть")
        self.assertEqual(len(network_items["Сеть"]), 2)

    def test_low_stock_detection(self):
        self.service.create_product("Дефицитный товар", 3, 500.0)
        self.service.create_product("Достаточный товар", 25, 100.0)

        low = self.service.get_low_stock_products(threshold=10)
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0].name, "Дефицитный товар")


if __name__ == "__main__":
    unittest.main()
