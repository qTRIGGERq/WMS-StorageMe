"""
Пользовательский интерфейс консольного приложения (Presentation Layer).
Отвечает исключительно за отображение данных, меню и считывание ввода от пользователя.
"""

import sys
from typing import Optional

from storage_me.exceptions import (
    DuplicateProductError,
    InvalidPriceError,
    InvalidQuantityError,
    ProductNotFoundError,
    StorageError,
    ValidationError,
    WMSException,
)
from storage_me.repositories.base import BaseWarehouseRepository
from storage_me.repositories.json_repository import JsonWarehouseRepository
from storage_me.services.warehouse_service import WarehouseService


class WarehouseApp:
    """
    Консольное приложение для управления складом WMS-StorageMe.
    Организует интерактивный цикл работы пользователя с меню и командами.
    """

    def __init__(self, repository: Optional[BaseWarehouseRepository] = None):
        self._repository = repository or JsonWarehouseRepository()
        self._service = WarehouseService(self._repository)

    @property
    def service(self) -> WarehouseService:
        return self._service

    def run(self) -> None:
        """Главный интерактивный цикл приложения."""
        print("\n" + "=" * 56)
        print("   ДОБРО ПОЖАЛОВАТЬ В СИСТЕМУ WMS-StorageMe v2.0")
        print("   Курсовой проект: ООП на интерпретируемых языках")
        print("=" * 56)

        while True:
            try:
                self._show_menu()
                choice = input("\n👉 Выберите действие (1-9): ").strip()

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
                    print("\n👋 Работа с системой WMS-StorageMe завершена. До свидания!")
                    break
                else:
                    print("⚠️ Неверный выбор! Пожалуйста, выберите пункт меню от 1 до 9.")
            except (KeyboardInterrupt, EOFError):
                print("\n\n👋 Сеанс прерван пользователем. До свидания!")
                break
            except StorageError as e:
                print(f"❌ Критическая ошибка хранилища данных: {e}")
            except Exception as e:
                print(f"❌ Непредвиденная ошибка в работе интерфейса: {e}")

    def _show_menu(self) -> None:
        print("\n" + "=" * 56)
        print("🏢              МЕНЮ УПРАВЛЕНИЯ СКЛАДОМ")
        print("=" * 56)
        print(" 1. ➕ Создать новый товар")
        print(" 2. 📦 Просмотреть каталог товаров")
        print(" 3. 📝 Изменить количество (приход / отгрузка)")
        print(" 4. ✏️  Редактировать параметры товара")
        print(" 5. 🔍 Поиск товаров по наименованию")
        print(" 6. 📋 Журнал аудита движений запасов")
        print(" 7. 📊 Аналитика и статистика склада")
        print(" 8. 🗑️  Удалить товар из системы")
        print(" 9. 🚪 Выход из программы")
        print("=" * 56)

    def _create_product(self) -> None:
        print("\n" + "-" * 56)
        print("➕ СОЗДАНИЕ НОВОГО ТОВАРА")
        print("-" * 56)

        name = input("Введите наименование товара: ").strip()
        if not name:
            print("❌ Наименование не может быть пустым!")
            return

        qty_input = input("Введите количество: ").strip()
        try:
            quantity = int(qty_input)
            if quantity < 0:
                print("❌ Количество не может быть отрицательным!")
                return
        except ValueError:
            print("❌ Количество должно быть целым числом!")
            return

        price_input = input("Введите цену за единицу (руб.): ").strip()
        try:
            price = float(price_input.replace(',', '.'))
            if price < 0:
                print("❌ Цена не может быть отрицательной!")
                return
        except ValueError:
            print("❌ Цена должна быть числом!")
            return

        category = input("Введите категорию товара [по умолчанию 'Без категории']: ").strip()
        location = input("Введите место хранения (стеллаж/ячейка) [по умолчанию 'Не указано']: ").strip()

        try:
            product = self._service.create_product(
                name=name,
                quantity=quantity,
                price=price,
                category=category or "Без категории",
                location=location or "Не указано"
            )
            print("\n✅ Товар успешно добавлен в систему!")
            print(f"   ID:          {product.id}")
            print(f"   Товар:       {product.name}")
            print(f"   Количество:  {product.quantity} шт.")
            print(f"   Цена:        {product.price:.2f} ₽")
            print(f"   Стоимость:   {product.total_value():.2f} ₽")
            print(f"   Категория:   {product.category}")
            print(f"   Место:       {product.location}")
        except DuplicateProductError as e:
            print(f"❌ {e}")
        except ValidationError as e:
            print(f"❌ Ошибка валидации данных: {e}")

    def _view_all_products(self) -> None:
        print("\n" + "-" * 56)
        print("📦 КАТАЛОГ ТОВАРОВ НА СКЛАДЕ")
        print("-" * 56)

        products = self._service.get_all_products()
        if not products:
            print("📭 На складе нет зарегистрированных товаров.")
            return

        total_value = 0.0
        total_quantity = 0

        for i, prod in enumerate(products, 1):
            print(f"\n[{i}] {prod.name}")
            print(f"    ├─ ID:         {prod.id}")
            print(f"    ├─ Остаток:    {prod.quantity} шт." + (" ⚠️ (МАЛО)" if prod.is_low_stock() else ""))
            print(f"    ├─ Цена ед.:   {prod.price:.2f} ₽")
            print(f"    ├─ Сумма:      {prod.total_value():.2f} ₽")
            print(f"    ├─ Категория:  {prod.category}")
            print(f"    ├─ Размещение: {prod.location}")
            print(f"    └─ Изменен:    {prod.updated_at.strftime('%Y-%m-%d %H:%M')}")

            total_value += prod.total_value()
            total_quantity += prod.quantity

        print("\n" + "-" * 56)
        print(f"📊 Всего позиций в каталоге: {len(products)}")
        print(f"🔢 Суммарный объем товаров:  {total_quantity} шт.")
        print(f"💰 Общая оценочная стоимость: {total_value:,.2f} ₽".replace(',', ' '))
        print("-" * 56)

    def _update_quantity(self) -> None:
        print("\n" + "-" * 56)
        print("📝 ОБНОВЛЕНИЕ ОСТАТКОВ (ПРИХОД / СПИСАНИЕ)")
        print("-" * 56)

        name = input("Введите наименование товара: ").strip()
        if not name:
            print("❌ Наименование не может быть пустым!")
            return

        product = self._service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден на складе!")
            return

        print(f"Найден товар: {product.name} (текущий остаток: {product.quantity} шт.)")

        qty_input = input("Введите новое количество на складе: ").strip()
        try:
            new_quantity = int(qty_input)
            if new_quantity < 0:
                print("❌ Количество не может быть отрицательным!")
                return
        except ValueError:
            print("❌ Введите корректное целое число!")
            return

        reason = input("Укажите причину изменения (накладная, инвентаризация, брак): ").strip()

        try:
            old_qty = product.quantity
            self._service.update_product_quantity(name, new_quantity, reason)
            delta = new_quantity - old_qty
            delta_str = f"+{delta}" if delta > 0 else str(delta)
            print(f"✅ Остаток товара '{product.name}' успешно изменен: {old_qty} → {new_quantity} ({delta_str} шт.)")
        except WMSException as e:
            print(f"❌ {e}")

    def _update_product_info(self) -> None:
        print("\n" + "-" * 56)
        print("✏️  РЕДАКТИРОВАНИЕ ПАРАМЕТРОВ ТОВАРА")
        print("-" * 56)

        name = input("Введите наименование товара для изменения: ").strip()
        if not name:
            print("❌ Наименование не может быть пустым!")
            return

        product = self._service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден!")
            return

        print(f"\nРедактирование карточки: {product.name}")
        print(f"  • Текущая цена:       {product.price:.2f} ₽")
        print(f"  • Текущая категория:  {product.category}")
        print(f"  • Текущее размещение: {product.location}")
        print("\n(Нажмите Enter, чтобы оставить поле без изменений)")

        updates = {}

        new_name = input("Новое наименование: ").strip()
        if new_name:
            updates['name'] = new_name

        price_str = input("Новая цена: ").strip()
        if price_str:
            try:
                price_val = float(price_str.replace(',', '.'))
                if price_val < 0:
                    print("❌ Цена не может быть отрицательной!")
                    return
                updates['price'] = price_val
            except ValueError:
                print("❌ Некорректный формат цены!")
                return

        cat = input("Новая категория: ").strip()
        if cat:
            updates['category'] = cat

        loc = input("Новое место хранения: ").strip()
        if loc:
            updates['location'] = loc

        if not updates:
            print("ℹ️ Изменения не внесены.")
            return

        try:
            updated_prod = self._service.update_product_info(name, **updates)
            print(f"✅ Карточка товара '{updated_prod.name}' успешно обновлена!")
        except WMSException as e:
            print(f"❌ Ошибка обновления: {e}")

    def _search_products(self) -> None:
        print("\n" + "-" * 56)
        print("🔍 ПОИСК ТОВАРОВ В КАТАЛОГЕ")
        print("-" * 56)

        query = input("Введите поисковый запрос (часть наименования): ").strip()
        if not query:
            print("❌ Поисковый запрос не может быть пустым!")
            return

        results = self._service.search_products_by_name(query)
        if not results:
            print(f"🔎 По запросу '{query}' совпадений не обнаружено.")
            return

        print(f"\n🔎 Найдено товаров: {len(results)}")
        for i, prod in enumerate(results, 1):
            print(f"  [{i}] {prod.name} | Остаток: {prod.quantity} шт. | "
                  f"Цена: {prod.price:.2f} ₽ | Категория: {prod.category} | Место: {prod.location}")

    def _view_movements(self) -> None:
        print("\n" + "-" * 56)
        print("📋 ЖУРНАЛ АУДИТА ДВИЖЕНИЯ ЗАПАСОВ")
        print("-" * 56)

        movements = self._service.get_movements_history(limit=25)
        if not movements:
            print("📭 Журнал операций пуст.")
            return

        print(f"Показано последних записей: {len(movements)}\n")
        for m in movements:
            print(f"  {m}")

    def _show_statistics(self) -> None:
        print("\n" + "-" * 56)
        print("📊 СВОДНАЯ СТАТИСТИКА И АНАЛИТИКА СКЛАДА")
        print("-" * 56)

        stats = self._service.get_statistics()
        if stats['total_products'] == 0:
            print("📭 Склад пуст, статистика недоступна.")
            return

        print(f"• Всего наименований (SKU): {stats['total_products']}")
        print(f"• Суммарное количество единиц: {stats['total_quantity']} шт.")
        print(f"• Оценочная стоимость запасов: {stats['total_value']:,.2f} ₽".replace(',', ' '))

        if stats['most_expensive']:
            me = stats['most_expensive']
            print(f"• Самая дорогая позиция:     {me.name} ({me.price:.2f} ₽/шт.)")

        if stats['largest_quantity']:
            lq = stats['largest_quantity']
            print(f"• Самый массовый товар:      {lq.name} ({lq.quantity} шт.)")

        # Категории
        categories = self._service.get_products_by_category()
        print("\n📁 Распределение по категориям:")
        for cat, prods in categories.items():
            cat_qty = sum(p.quantity for p in prods)
            cat_sum = sum(p.total_value() for p in prods)
            print(f"   - {cat}: {len(prods)} SKU, {cat_qty} шт., сумма: {cat_sum:,.2f} ₽".replace(',', ' '))

        # Критический остаток
        low_stock = self._service.get_low_stock_products(threshold=10)
        if low_stock:
            print("\n⚠️ ВНИМАНИЕ: Товары с критическим остатком (< 10 шт.):")
            for lp in low_stock:
                print(f"   ! {lp.name}: осталось всего {lp.quantity} шт. (Место: {lp.location})")
        else:
            print("\n✅ Все складские остатки находятся в норме (нет позиций < 10 шт.).")

    def _delete_product(self) -> None:
        print("\n" + "-" * 56)
        print("🗑️  УДАЛЕНИЕ ТОВАРА СО СКЛАДА")
        print("-" * 56)

        name = input("Введите наименование товара для удаления: ").strip()
        if not name:
            print("❌ Наименование не может быть пустым!")
            return

        product = self._service.get_product_by_name(name)
        if not product:
            print(f"❌ Товар '{name}' не найден!")
            return

        print(f"\nБудет удален товар: {product.name}")
        print(f"  Остаток к списанию: {product.quantity} шт.")
        print(f"  Суммарная стоимость: {product.total_value():.2f} ₽")

        confirm = input("\nПодтверждаете удаление? (да/нет): ").strip().lower()
        if confirm in ('да', 'yes', 'y'):
            reason = input("Укажите причину списания/удаления: ").strip()
            try:
                self._service.delete_product(name, reason=reason or "Удаление товара со склада")
                print(f"✅ Товар '{name}' успешно удален из системы!")
            except WMSException as e:
                print(f"❌ Ошибка удаления: {e}")
        else:
            print("🚫 Операция удаления отменена пользователем.")
