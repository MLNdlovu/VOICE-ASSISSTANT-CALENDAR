"""Compatibility shim: re-export from `src.voice_handler` for legacy imports."""
from src.voice_handler import *

__all__ = getattr(__import__('src.voice_handler', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
