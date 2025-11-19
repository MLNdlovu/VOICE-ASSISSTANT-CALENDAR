"""Compatibility shim for legacy imports.
Re-export get_details functions from `src.get_details`.
"""
from src.get_details import *

__all__ = getattr(__import__('src.get_details', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
