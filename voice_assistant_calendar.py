"""Compatibility shim for legacy imports.
Re-export functions from `src.voice_assistant_calendar` used by tests.
"""
from src.voice_assistant_calendar import *

__all__ = getattr(__import__('src.voice_assistant_calendar', fromlist=['*']), '__all__', None) or [name for name in dir() if not name.startswith('_')]
