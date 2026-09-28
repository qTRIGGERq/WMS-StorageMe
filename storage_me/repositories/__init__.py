"""
Модуль уровня доступа к данным (Repository Layer).
"""

from storage_me.repositories.base import BaseWarehouseRepository
from storage_me.repositories.json_repository import JsonWarehouseRepository

__all__ = ["BaseWarehouseRepository", "JsonWarehouseRepository"]
