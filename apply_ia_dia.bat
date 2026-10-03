@echo off
rem Apply penggantian "ia" -> "dia" pada terjemahan + reinsert .binu8
rem (aturan: "ia" hanya untuk benda mati; orang memakai "dia")
chcp 65001 >nul
python "%~dp0ia_dia_fix.py" status
echo.
set /p LANJUT="Terapkan sekarang? (y/N): "
if /i "%LANJUT%"=="y" (
    python "%~dp0ia_dia_fix.py" apply
)
pause
