"""Compatibility shim for legacy imports.
Re-export booking helpers from `src.book`.
"""
from src.book import *

__all__ = getattr(__import__('src.book', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
