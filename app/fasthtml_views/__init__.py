"""FastHTML views for ProAlgoTrader.

This module provides FastHTML-based views that parallel the existing Jinja2 templates.
"""

from .components import (
    confirmation_modal,
    get_modal_styles,
    get_sync_button_styles,
)
from .router import router

__all__ = [
    "router",
    "confirmation_modal",
    "get_modal_styles",
    "get_sync_button_styles",
]
