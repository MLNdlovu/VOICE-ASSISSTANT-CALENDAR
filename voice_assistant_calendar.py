"""Compatibility shim for legacy imports.

Re-export functions from `src.voice_assistant_calendar` used by tests.
This module exists so tests and legacy code can import `voice_assistant_calendar`
from the project root while the real implementation lives under `src/`.
"""
from src.voice_assistant_calendar import authenticate, config_command, load_voice_assistant_calendar
from googleapiclient.discovery import build

__all__ = ["authenticate", "config_command", "load_voice_assistant_calendar", "build"]
