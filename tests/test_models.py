"""
Модульные тесты доменных моделей (Product, StockMovement).
"""

import unittest
from datetime import datetime

from storage_me.exceptions import InvalidPriceError, InvalidQuantityError, ValidationError
from storage_me.models.movement import MovementType, StockMovement
from storage_me.models.product import Product


class TestProductModel(unittest.TestCase):

    def test_create_valid_product(self):
        prod = Product(name="Монитор 24\"", quantity=10, price=15000.0, category="Электроника", location="Стеллаж A")
        self.assertEqual(prod.name, "Монитор 24\"")
        self.assertEqual(prod.quantity, 10)
        self.assertEqual(prod.price, 15000.0)
        self.assertEqual(prod.category, "Электроника")
        self.assertEqual(prod.location, "Стеллаж A")
        self.assertEqual(prod.total_value(), 150000.0)
        self.assertFalse(prod.is_low_stock(threshold=5))
        self.assertIsNotNone(prod.id)
        self.assertIsInstance(prod.created_at, datetime)

    def test_empty_name_validation(self):
        with self.assertRaises(ValidationError):
            Product(name="   ", quantity=5, price=100.0)

    def test_negative_quantity_validation(self):
        with self.assertRaises(InvalidQuantityError):
            Product(name="Товар", quantity=-1, price=100.0)

    def test_negative_price_validation(self):
        with self.assertRaises(InvalidPriceError):
            Product(name="Товар", quantity=5, price=-50.0)

    def test_serialization_and_deserialization(self):
        prod = Product(name="Мышь", quantity=15, price=850.50, category="Периферия", location="B-1")
        d = prod.to_dict()
        self.assertEqual(d['name'], "Мышь")
        self.assertEqual(d['quantity'], 15)
        self.assertEqual(d['price'], 850.50)

        restored = Product.from_dict(d)
        self.assertEqual(restored.id, prod.id)
        self.assertEqual(restored.name, prod.name)
        self.assertEqual(restored.quantity, prod.quantity)
        self.assertEqual(restored.price, prod.price)


class TestStockMovementModel(unittest.TestCase):

    def test_create_movement(self):
        prod = Product(name="Клавиатура", quantity=20, price=2000.0)
        mov = StockMovement(
            movement_type=MovementType.ADD,
            product=prod,
            quantity=20,
            reason="Начальный остаток"
        )
        self.assertEqual(mov.type, MovementType.ADD)
        self.assertEqual(mov.quantity, 20)
        self.assertEqual(mov.product_id, prod.id)
        self.assertEqual(mov.product_name, "Клавиатура")
        self.assertIn("➕", mov.get_type_symbol())


if __name__ == "__main__":
    unittest.main()
