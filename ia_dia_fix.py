# -*- coding: utf-8 -*-
"""ia_dia_fix — apply/deapply penggantian kata "ia" -> "dia" pada terjemahan.

Implementasi: ``src/nexas/ia_dia_fix.py``. Wrapper kompatibilitas root agar
perintah pendek (``python ia_dia_fix.py status|apply|deapply``) tetap jalan.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.nexas.ia_dia_fix import *  # noqa: F401,F403
from src.nexas.ia_dia_fix import main  # noqa: F401

if __name__ == '__main__':
    main()
