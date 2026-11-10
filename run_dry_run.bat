@echo off
cd /d "%~dp0"
echo Menjalankan Auto-Scrolling Hand Controller (Mode Latihan / Dry-Run)...
uv run --python 3.12 python -m auto_scrolling.main --dry-run
pause
