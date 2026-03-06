#!/usr/bin/env bash
set -o errexit
pip install -r requirements.txt
# Чтобы не было 404 на /static/css/custom.css: создаём каталог, если его нет в репо
mkdir -p kvant_site/static/css
[ -f kvant_site/static/css/custom.css ] || echo "/* placeholder */" > kvant_site/static/css/custom.css
python manage.py migrate --noinput
# Страницы сайта (новости, о нас, квантумы) — безопасно при повторном запуске
python manage.py populate_site || true
python manage.py populate_quantums || true
python manage.py collectstatic --noinput
