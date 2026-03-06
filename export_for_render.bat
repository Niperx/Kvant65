@echo off
chcp 65001 >nul
echo Экспорт данных из SQLite для переноса на Render...
echo Используются настройки dev (db.sqlite3).
echo.

set DJANGO_SETTINGS_MODULE=kvant_site.settings.dev
python manage.py dumpdata --natural-foreign --natural-primary -e contenttypes -e auth.Permission -e sessions --indent 2 -o data.json

if %ERRORLEVEL% NEQ 0 (
    echo Ошибка экспорта.
    pause
    exit /b 1
)

echo.
echo Готово: создан файл data.json
echo Дальше: закоммитьте data.json и задеплойте; в Render Shell выполните:
echo   python manage.py loaddata data.json
echo.
pause
