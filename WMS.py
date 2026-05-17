import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import uuid


# ==================== 1. Модель товара (Entity) ====================
class Product:

    def __init__(self, name: str, quantity: int, price: float,
                 category: str, location: str, product_id: str = None):
        self._id = product_id or str(uuid.uuid4())[:8]  # Автогенерация ID если не указан
        self._name = name
        self._quantity = quantity
        self._price = price
        self._category = category
        self._location = location
        self._created_at = datetime.now()
        self._updated_at = datetime.now()

    # Геттеры
    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def price(self) -> float:
        return self._price

    @property
    def category(self) -> str:
        return self._category

    @property
    def location(self) -> str:
        return self._location

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # Сеттеры с валидацией
    @quantity.setter
    def quantity(self, value: int):
        if value < 0:
            raise ValueError("Количество не может быть отрицательным")
        self._quantity = value
        self._updated_at = datetime.now()

    @price.setter
    def price(self, value: float):
        if value < 0:
            raise ValueError("Цена не может быть отрицательной")
        self._price = value
        self._updated_at = datetime.now()

    @name.setter
    def name(self, value: str):
        if not value or not value.strip():
            raise ValueError("Название не может быть пустым")
        self._name = value.strip()
        self._updated_at = datetime.now()

    @category.setter
    def category(self, value: str):
        self._category = value.strip() if value else "Без категории"
        self._updated_at = datetime.now()

    @location.setter
    def location(self, value: str):
        self._location = value.strip() if value else "Не указано"
        self._updated_at = datetime.now()

    def total_value(self) -> float:
        return self._quantity * self._price

    def to_dict(self) -> dict:
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
    def from_dict(cls, data: dict) -> 'Product':
        product = cls(
            name=data['name'],
            quantity=data['quantity'],
            price=data['price'],
            category=data['category'],
            location=data['location'],
            product_id=data['id']
        )
        product._created_at = datetime.fromisoformat(data['created_at'])
        product._updated_at = datetime.fromisoformat(data['updated_at'])
        return product

    def __str__(self) -> str:
        return f"{self._name} (ID: {self._id}) - {self._quantity} шт., {self._price} руб."


# ==================== 2. Модель движения товара ====================
class MovementType:
    ADD = "ADD"
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    DELETE = "DELETE"


class StockMovement:

    def __init__(self, movement_type: str, product: Product,
                 quantity: int, reason: str):
        self._timestamp = datetime.now()
        self._type = movement_type
        self._product = product
        self._quantity = quantity
        self._reason = reason

    @property
    def timestamp(self) -> datetime:
        return self._timestamp

    @property
    def type(self) -> str:
        return self._type

    @property
    def product(self) -> Product:
        return self._product

    @property
    def quantity(self) -> int:
        return self._quantity

    @property
    def reason(self) -> str:
        return self._reason

    def to_dict(self) -> dict:
        return {
            'timestamp': self._timestamp.isoformat(),
            'type': self._type,
            'product_id': self._product.id,
            'product_name': self._product.name,
            'quantity': self._quantity,
            'reason': self._reason
        }

    @classmethod
    def from_dict(cls, data: dict, products: Dict[str, Product]) -> 'StockMovement':
        movement = cls(
            movement_type=data['type'],
            product=products[data['product_id']],
            quantity=data['quantity'],
            reason=data['reason']
        )
        movement._timestamp = datetime.fromisoformat(data['timestamp'])
        return movement

    def get_type_symbol(self) -> str:
        symbols = {
            MovementType.ADD: "➕",
            MovementType.INCREASE: "⬆️",
            MovementType.DECREASE: "⬇️",
            MovementType.DELETE: "🗑️"
        }
        return symbols.get(self._type, "➡️")

    def __str__(self) -> str:
        return f"{self._timestamp.strftime('%Y-%m-%d %H:%M')} {self.get_type_symbol()} {self._product.name}: {self._quantity} шт. ({self._reason})"


# ==================== 3. Репозиторий (работа с данными) ====================
class WarehouseRepository:

    def __init__(self, data_file: str = "warehouse_data.json"):
        self._data_file = data_file

    def load(self) -> tuple[Dict[str, Product], List[StockMovement]]:
        products = {}
        movements = []

        if os.path.exists(self._data_file):
            try:
                with open(self._data_file, 'r', encoding='utf-8') as file:
                    data = json.load(file)

                    products_data = data.get('products', {})
                    for product_id, product_dict in products_data.items():
                        products[product_id] = Product.from_dict(product_dict)

                    movements_data = data.get('movements', [])
                    for movement_dict in movements_data:
                        if movement_dict['product_id'] in products:
                            movement = StockMovement.from_dict(movement_dict, products)
                            movements.append(movement)

                print(f"✅ Загружено {len(products)} товаров и {len(movements)} записей истории")
                return products, movements

            except Exception as e:
                print(f"❌ Ошибка загрузки данных: {e}")

        return products, movements

    def save(self, products: Dict[str, Product], movements: List[StockMovement]) -> None:
        try:
            data = {
                'products': {pid: product.to_dict() for pid, product in products.items()},
                'movements': [movement.to_dict() for movement in movements]
            }
            with open(self._data_file, 'w', encoding='utf-8') as file:
                json.dump(data, file, ensure_ascii=False, indent=2)
            print("✅ Данные сохранены")
        except Exception as e:
            print(f"❌ Ошибка сохранения данных: {e}")


# ==================== 4. Сервис (бизнес-логика) ====================
class WarehouseService:

    def __init__(self, repository: WarehouseRepository):
        self._repository = repository
        self._products, self._stock_movements = self._repository.load()

    @property
    def products(self) -> Dict[str, Product]:
        return self._products

    @property
    def stock_movements(self) -> List[StockMovement]:
        return self._stock_movements

    def create_product(self, name: str, quantity: int, price: float,
                       category: str, location: str) -> Optional[Product]:
        try:
            for product in self._products.values():
                if product.name.lower() == name.lower():
                    print(f"❌ Товар с именем '{name}' уже существует!")
                    return None

            product = Product(name, quantity, price, category, location)
            self._products[product.id] = product

            movement = StockMovement(MovementType.ADD, product, quantity, "Начальный остаток")
            self._stock_movements.append(movement)

            self._trim_movements_history()
            self._repository.save(self._products, self._stock_movements)
            return product

        except Exception as e:
            print(f"❌ Ошибка создания товара: {e}")
            return None

    def get_product_by_name(self, name: str) -> Optional[Product]:
        name_lower = name.lower()
        for product in self._products.values():
            if product.name.lower() == name_lower:
                return product
        return None

    def search_products_by_name(self, search_term: str) -> List[Product]:
        search_term = search_term.lower()
        results = []
        for product in self._products.values():
            if search_term in product.name.lower():
                results.append(product)
        return results

    def update_product_quantity(self, product_name: str, new_quantity: int, reason: str) -> bool:
        try:
            product = self.get_product_by_name(product_name)
            if not product:
                print(f"❌ Товар '{product_name}' не найден!")
                return False

            old_quantity = product.quantity
            difference = new_quantity - old_quantity

            if difference == 0:
                print("ℹ️ Количество не изменилось")
                return False

            product.quantity = new_quantity

            movement_type = MovementType.INCREASE if difference > 0 else MovementType.DECREASE
            movement = StockMovement(movement_type, product, abs(difference), reason)
            self._stock_movements.append(movement)

            self._trim_movements_history()
            self._repository.save(self._products, self._stock_movements)
            print(f"✅ Количество товара '{product_name}' обновлено: {old_quantity} → {new_quantity}")
            return True

        except Exception as e:
            print(f"❌ Ошибка обновления количества: {e}")
            return False

    def update_product_info(self, product_name: str, **kwargs) -> bool:
        try:
            product = self.get_product_by_name(product_name)
            if not product:
                print(f"❌ Товар '{product_name}' не найден!")
                return False

            old_name = product.name

            if 'name' in kwargs and kwargs['name']:
                for p in self._products.values():
                    if p.name.lower() == kwargs['name'].lower() and p.id != product.id:
                        print(f"❌ Товар с именем '{kwargs['name']}' уже существует!")
                        return False
                product.name = kwargs['name']

            if 'price' in kwargs and kwargs['price'] is not None:
                product.price = kwargs['price']

            if 'category' in kwargs and kwargs['category']:
                product.category = kwargs['category']

            if 'location' in kwargs and kwargs['location']:
                product.location = kwargs['location']

            self._repository.save(self._products, self._stock_movements)
            new_name = product.name if 'name' in kwargs else old_name
            print(f"✅ Информация о товаре '{new_name}' обновлена")
            return True

        except Exception as e:
            print(f"❌ Ошибка обновления информации: {e}")
            return False

    def delete_product(self, product_name: str) -> bool:
        try:
            product = self.get_product_by_name(product_name)
            if not product:
                print(f"❌ Товар '{product_name}' не найден!")
                return False

            movement = StockMovement(MovementType.DELETE, product, product.quantity, "Удаление товара")
            self._stock_movements.append(movement)

            del self._products[product.id]

            self._trim_movements_history()
            self._repository.save(self._products, self._stock_movements)
            print(f"✅ Товар '{product_name}' удален")
            return True

        except Exception as e:
            print(f"❌ Ошибка удаления товара: {e}")
            return False

    def get_all_products(self) -> List[Product]:
        return list(self._products.values())

    def get_products_by_category(self, category: str = None) -> Dict[str, List[Product]]:
        if category:
            result = {}
            for product in self._products.values():
                if product.category.lower() == category.lower():
                    result[product.category] = result.get(product.category, []) + [product]
            return result
        else:
            categories = {}
            for product in self._products.values():
                cat = product.category
                categories[cat] = categories.get(cat, []) + [product]
            return categories

    def get_low_stock_products(self, threshold: int = 10) -> List[Product]:
        return [p for p in self._products.values() if p.quantity < threshold]

    def get_statistics(self) -> dict:
        total_products = len(self._products)
        total_quantity = sum(p.quantity for p in self._products.values())
        total_value = sum(p.total_value() for p in self._products.values())

        most_expensive = max(self._products.values(), key=lambda p: p.price) if self._products else None

        largest_quantity = max(self._products.values(), key=lambda p: p.quantity) if self._products else None

        return {
            'total_products': total_products,
            'total_quantity': total_quantity,
            'total_value': total_value,
            'most_expensive': most_expensive,
            'largest_quantity': largest_quantity
        }

    def get_movements_history(self, limit: int = 20) -> List[StockMovement]:
        return self._stock_movements[-limit:] if limit > 0 else self._stock_movements

    def _trim_movements_history(self, max_records: int = 100):
        if len(self._stock_movements) > max_records:
            self._stock_movements = self._stock_movements[-max_records:]


# ==================== 5. Консольное приложение ====================
class WarehouseApp:

    def __init__(self):
        self.repository = WarehouseRepository()
        self.service = WarehouseService(self.repository)

    def run(self):
        while True:
            self._show_menu()
            choice = input("\nВыберите действие (1-9): ").strip()

            if choice == '1':
                self._create_product()
            elif choice == '2':
                self._view_all_products()
            elif choice == '3':
                self._update_quantity()
            elif choice == '4':
                self._update_product_info()
            elif choice == '5':
                self._search_products()
            elif choice == '6':
                self._view_movements()
            elif choice == '7':
                self._show_statistics()
            elif choice == '8':
                self._delete_product()
            elif choice == '9':
                print("\n👋 До свидания!")
                break
            else:
                print("❌ Неверный выбор! Пожалуйста, выберите 1-9")

    def _show_menu(self):
        print("\n" + "=" * 50)
        print("🏢 СИСТЕМА УПРАВЛЕНИЯ СКЛАДОМ")
        print("=" * 50)
        print("1. ➕ Создать товар")
        print("2. 📦 Просмотреть все товары")
        print("3. 📝 Обновить количество товара")
        print("4. ✏️ Редактировать информацию о товаре")
        print("5. 🔍 Поиск товаров по имени")
        print("6. 📋 История движений")
        print("7. 📊 Статистика склада")
        print("8. 🗑️ Удалить товар")
        print("9. 🚪 Выход")
        print("=" * 50)

    def _create_product(self):
        print("\n" + "=" * 50)
        print("➕ СОЗДАНИЕ НОВОГО ТОВАРА")
        print("=" * 50)

        name = input("Введите название товара: ").strip()
        if not name:
            print("❌ Название не может быть пустым!")
            return

        try:
            quantity = int(input("Введите количество: "))
            if quantity < 0:
                print("❌ Количество не может быть отрицательным!")
                return
        except ValueError:
            print("❌ Введите корректное число!")
            return

        try:
            price = float(input("Введите цену за единицу: "))
            if price < 0:
                print("❌ Цена не может быть отрицательной!")
                return
        except ValueError:
            print("❌ Введите корректную цену!")
            return

        category = input("Введите категорию товара: ").strip()
        location = input("Введите место хранения: ").strip()

        product = self.service.create_product(name, quantity, price, category, location)
        if product:
            print(f"\n✅ Товар успешно создан!")
            print(f"   ID товара: {product.id}")
            print(f"   Название: {product.name}")
            print(f"   Количество: {product.quantity}")
            print(f"   Цена: {product.price} руб.")

    def _view_all_products(self):
        print("\n" + "=" * 50)
        print("📦 ВСЕ ТОВАРЫ НА СКЛАДЕ")
        print("=" * 50)

        products = self.service.get_all_products()
        if not products:
            print("📭 Склад пуст")
            return

        total_value = 0
        total_items = 0

        for i, product in enumerate(products, 1):
            print(f"\n{i}. {product.name}")
            print(f"   ID: {product.id}")
            print(f"   Количество: {product.quantity} шт.")
            print(f"   Цена: {product.price} руб.")
            print(f"   Общая стоимость: {product.total_value():.2f} руб.")
            print(f"   Категория: {product.category}")
            print(f"   Место: {product.location}")
            print(f"   Обновлено: {product.updated_at.strftime('%Y-%m-%d %H:%M')}")
            print("-" * 40)

            total_value += product.total_value()
            total_items += product.quantity

        print(f"\n💰 Общая стоимость всех товаров: {total_value:.2f} руб.")
        print(f"📊 Всего позиций: {len(products)}")
        print(f"🔢 Всего единиц товара: {total_items}")

    def _update_quantity(self):
        print("\n" + "=" * 50)
        print("📝 ОБНОВЛЕНИЕ КОЛИЧЕСТВА ТОВАРА")
        print("=" * 50)

        name = input("Введите название товара: ").strip()
        if not name:
            print("❌ Название не может быть пустым!")
            return

        product = self.service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден!")
            return

        print(f"\nТекущий товар: {product.name}")
        print(f"Текущее количество: {product.quantity}")

        try:
            new_quantity = int(input("Введите новое количество: "))
            if new_quantity < 0:
                print("❌ Количество не может быть отрицательным!")
                return
        except ValueError:
            print("❌ Введите корректное число!")
            return

        reason = input("Укажите причину изменения: ").strip()
        self.service.update_product_quantity(name, new_quantity, reason)

    def _update_product_info(self):
        print("\n" + "=" * 50)
        print("✏️ РЕДАКТИРОВАНИЕ ТОВАРА")
        print("=" * 50)

        name = input("Введите название товара для редактирования: ").strip()
        if not name:
            print("❌ Название не может быть пустым!")
            return

        product = self.service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден!")
            return

        print(f"\nРедактирование товара: {product.name}")
        print(f"Текущая цена: {product.price} руб.")
        print(f"Текущая категория: {product.category}")
        print(f"Текущее место: {product.location}")

        updates = {}

        new_name = input("\nНовое название (оставьте пустым для пропуска): ").strip()
        if new_name:
            updates['name'] = new_name

        price_input = input("Новая цена (оставьте пустым для пропуска): ").strip()
        if price_input:
            try:
                updates['price'] = float(price_input)
                if updates['price'] < 0:
                    print("❌ Цена не может быть отрицательной!")
                    return
            except ValueError:
                print("❌ Введите корректную цену!")
                return

        category = input("Новая категория (оставьте пустым для пропуска): ").strip()
        if category:
            updates['category'] = category

        location = input("Новое место хранения (оставьте пустым для пропуска): ").strip()
        if location:
            updates['location'] = location

        if updates:
            self.service.update_product_info(name, **updates)
        else:
            print("ℹ️ Нет изменений для сохранения")

    def _search_products(self):
        print("\n" + "=" * 50)
        print("🔍 ПОИСК ТОВАРОВ ПО ИМЕНИ")
        print("=" * 50)

        search_term = input("Введите название или часть названия: ").strip()
        if not search_term:
            print("❌ Введите поисковый запрос!")
            return

        results = self.service.search_products_by_name(search_term)

        if not results:
            print(f"🔎 Товары, содержащие '{search_term}', не найдены")
            return

        print(f"\n🔎 Найдено товаров: {len(results)}")
        for i, product in enumerate(results, 1):
            print(f"\n{i}. {product.name}")
            print(f"   ID: {product.id}")
            print(f"   Количество: {product.quantity} шт.")
            print(f"   Цена: {product.price} руб.")
            print(f"   Категория: {product.category}")
            print(f"   Место: {product.location}")

    def _view_movements(self):
        print("\n" + "=" * 50)
        print("📋 ИСТОРИЯ ДВИЖЕНИЙ ТОВАРОВ")
        print("=" * 50)

        movements = self.service.get_movements_history()
        if not movements:
            print("📭 История движений пуста")
            return

        for movement in movements:
            print(f"\n{movement}")

    def _show_statistics(self):
        print("\n" + "=" * 50)
        print("📊 СТАТИСТИКА СКЛАДА")
        print("=" * 50)

        if not self.service.get_all_products():
            print("📭 Склад пуст")
            return

        categories = self.service.get_products_by_category()
        print("\n📁 Товары по категориям:")
        for category, products in categories.items():
            print(f"  {category}: {len(products)} позиций")

        low_stock = self.service.get_low_stock_products()
        if low_stock:
            print("\n⚠️ Товары с низким остатком (< 10):")
            for product in low_stock:
                print(f"  {product.name}: {product.quantity} шт.")

        stats = self.service.get_statistics()
        print(f"\n📈 Общая статистика:")
        print(f"  Всего позиций: {stats['total_products']}")
        print(f"  Всего единиц: {stats['total_quantity']}")
        print(f"  Общая стоимость: {stats['total_value']:.2f} руб.")

        if stats['most_expensive']:
            print(f"\n💎 Самый дорогой товар:")
            print(f"  {stats['most_expensive'].name}: {stats['most_expensive'].price} руб.")

        if stats['largest_quantity']:
            print(f"\n📦 Самый многочисленный товар:")
            print(f"  {stats['largest_quantity'].name}: {stats['largest_quantity'].quantity} шт.")

    def _delete_product(self):
        print("\n" + "=" * 50)
        print("🗑️ УДАЛЕНИЕ ТОВАРА")
        print("=" * 50)

        name = input("Введите название товара для удаления: ").strip()
        if not name:
            print("❌ Название не может быть пустым!")
            return

        product = self.service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден!")
            return

        print(f"\nТовар: {product.name}")
        print(f"Количество: {product.quantity} шт.")
        print(f"Общая стоимость: {product.total_value():.2f} руб.")

        confirm = input("\nВы уверены, что хотите удалить товар? (да/нет): ").strip().lower()
        if confirm == 'да':
            self.service.delete_product(name)
        else:
            print("❌ Удаление отменено")


# ==================== 6. Точка входа ====================
def main():
    app = WarehouseApp()
    app.run()

if __name__ == "__main__":
    main()