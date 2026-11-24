# -*- coding: utf-8 -*-
"""ui.zahira_konusmalar — ui_zahira_konusmalar modülü için köprü.

web/main.py ve zahira_widget.py buradan import yapar.
Gerçek içerik proje kökündeki ui_zahira_konusmalar.py dosyasındadır.
"""
import sys
import os

# Proje kökünün sys.path'te olduğundan emin ol
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _root not in sys.path:
    sys.path.insert(0, _root)

from ui_zahira_konusmalar import (  # noqa: F401
    DIALOGUES,
    SPRITE_FILES,
    GENEL as GENERAL,   # web/main.py GENERAL adını bekliyor
    Zahira,
    Line,
    general,
    sprite_path,
)

__all__ = ["DIALOGUES", "SPRITE_FILES", "GENERAL", "Zahira", "Line", "general", "sprite_path"]
