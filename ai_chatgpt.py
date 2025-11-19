"""Compatibility shim: re-export from `src.ai_chatgpt` for legacy imports."""
from src.ai_chatgpt import *

__all__ = getattr(__import__('src.ai_chatgpt', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
