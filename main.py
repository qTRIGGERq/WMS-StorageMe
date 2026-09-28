#!/usr/bin/env python3
"""
Точка входа для запуска системы управления складом WMS-StorageMe.
"""

import sys
import os

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from storage_me.ui.console_app import WarehouseApp


def main():
    """Запуск консольного приложения."""
    app = WarehouseApp()
    app.run()


if __name__ == "__main__":
    main()
