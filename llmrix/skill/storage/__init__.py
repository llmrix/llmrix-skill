"""
storage: Abstract storage interface and concrete adapter implementations.
"""
from .base import BaseStorage
from .mysql import MySQLStorage

__all__ = ["BaseStorage", "MySQLStorage"]
