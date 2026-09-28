"""
Модульные тесты уровня доступа к данным (JsonWarehouseRepository).
"""

import os
import tempfile
import unittest

from storage_me.models.movement import MovementType, StockMovement
from storage_me.models.product import Product
from storage_me.repositories.json_repository import JsonWarehouseRepository


class TestJsonRepository(unittest.TestCase):

    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.temp_file.close()
        self.repo = JsonWarehouseRepository(data_file=self.temp_file.name)

    def tearDown(self):
        if os.path.exists(self.temp_file.name):
            os.remove(self.temp_file.name)

    def test_save_and_load_roundtrip(self):
        prod = Product(name="Тестовый товар", quantity=10, price=500.0, category="Тест", location="T-1")
        products = {prod.id: prod}
        mov = StockMovement(MovementType.ADD, prod, 10, "Первичное оприходование")
        movements = [mov]

        self.repo.save(products, movements)

        loaded_prods, loaded_movs = self.repo.load()
        self.assertEqual(len(loaded_prods), 1)
        self.assertEqual(len(loaded_movs), 1)

        loaded_prod = loaded_prods[prod.id]
        self.assertEqual(loaded_prod.name, "Тестовый товар")
        self.assertEqual(loaded_prod.quantity, 10)
        self.assertEqual(loaded_prod.price, 500.0)

        loaded_mov = loaded_movs[0]
        self.assertEqual(loaded_mov.quantity, 10)
        self.assertEqual(loaded_mov.reason, "Первичное оприходование")


if __name__ == "__main__":
    unittest.main()
