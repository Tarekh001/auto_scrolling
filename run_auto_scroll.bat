@echo off
cd /d "%~dp0"
echo Menjalankan Auto-Scrolling Hand Controller (Mode Aktif)...
uv run --python 3.12 python -m auto_scrolling.main
pause
