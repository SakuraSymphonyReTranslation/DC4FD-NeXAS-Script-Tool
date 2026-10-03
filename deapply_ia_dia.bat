@echo off
rem Batalkan penggantian "ia" -> "dia": pulihkan .binu8 dari backup
chcp 65001 >nul
python "%~dp0ia_dia_fix.py" deapply
pause
