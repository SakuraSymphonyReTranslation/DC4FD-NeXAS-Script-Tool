@echo off
title Update Patch D.C.4 Fortunate Departures

cd /d "%~dp0"

echo ===============================================================================
echo                   PEMBARUAN PATCH D.C.4 FORTUNATE DEPARTURES
echo ===============================================================================
echo.

if not exist "romfs\Script_Mod" (
    echo [ERROR] Folder romfs\Script_Mod tidak ditemukan!
    echo Silakan lakukan Insert Script terlebih dahulu.
    echo.
    pause
    exit /b 1
)

echo [*] Menyiapkan direktori patch...
set "PATCH_DIR=DC4FD_Indo_Patch\romfs"
set "EDEN_DIR=%APPDATA%\eden\load\010081E0161B2000\D.C.4 Fortunate Departures Patch\romfs"

if not exist "%PATCH_DIR%\Script" mkdir "%PATCH_DIR%\Script"
if not exist "%PATCH_DIR%\Config" mkdir "%PATCH_DIR%\Config"
if not exist "%EDEN_DIR%\Script" mkdir "%EDEN_DIR%\Script"
if not exist "%EDEN_DIR%\Config" mkdir "%EDEN_DIR%\Config"

echo [*] Menyalin file skrip terbaru ke folder patch lokal...
copy /y "romfs\Script_Mod\*.binu8" "%PATCH_DIR%\Script\" >nul

echo [*] Menyalin konfigurasi font kustom (system.datu8)...
if exist "romfs\Custom Config\system.datu8" copy /y "romfs\Custom Config\system.datu8" "%PATCH_DIR%\Config\" >nul

echo [*] Memperbarui patch langsung ke Emulator Eden...
copy /y "romfs\Script_Mod\*.binu8" "%EDEN_DIR%\Script\" >nul 2>nul
if errorlevel 1 (
    echo [!] Catatan: Jika emulator Eden sedang berjalan, tutup emulator terlebih dahulu agar file dapat ditimpa.
)
if exist "romfs\Custom Config\system.datu8" copy /y "romfs\Custom Config\system.datu8" "%EDEN_DIR%\Config\" >nul 2>nul

echo [*] Mengemas ulang file arsip DC4FD_Translation_Patch.zip...
python -c "import zipfile, os; from pathlib import Path; patch_dir = Path('DC4FD_Indo_Patch'); zip_path = 'DC4FD_Translation_Patch.zip'; z = zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED); [z.write(Path(r)/f, (Path(r)/f).relative_to(patch_dir.parent)) for r, d, fs in os.walk(patch_dir) for f in fs]; z.close(); size_mb = os.path.getsize(zip_path)/(1024*1024); print(f'    -> Selesai: DC4FD_Translation_Patch.zip ({size_mb:.2f} MB)')"

echo.
echo ===============================================================================
echo                           [SUKSES] PATCH DIPERBARUI!
echo ===============================================================================
echo.
echo LOKASI OUTPUT DAN STATUS:
echo.
echo [1] Emulator Eden (Terpasang dan Siap Dimainkan):
echo     %EDEN_DIR%
echo.
echo [2] Folder Mod Lokal (Struktur LayeredFS):
echo     %~dp0DC4FD_Indo_Patch\romfs
echo.
echo [3] File Arsip ZIP (Siap Dibagikan / Salin ke Nintendo Switch):
echo     %~dp0DC4FD_Translation_Patch.zip
echo.
echo ===============================================================================
echo.
pause
