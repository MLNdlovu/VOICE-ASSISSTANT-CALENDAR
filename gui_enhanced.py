"""Compatibility shim for legacy imports.
Re-exports symbols from `src/gui_enhanced.py` so tests and external scripts
that import `gui_enhanced` at top-level continue to work after refactor.
"""
from src.gui_enhanced import *

__all__ = getattr(__import__('src.gui_enhanced', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
