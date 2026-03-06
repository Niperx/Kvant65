# Деплой на Render

Проект настроен для развёртывания на [Render](https://render.com) с PostgreSQL.

## Что уже сделано

- **render.yaml** — описание сервиса (web + БД). Подключите репозиторий к Render через Blueprint.
- **kvant_site/settings/production.py** — продакшен-настройки (PostgreSQL, WhiteNoise, ALLOWED_HOSTS).
- **build.sh** — сборка: `pip install`, `collectstatic`, `migrate`.
- **requirements.txt** — добавлены gunicorn, whitenoise, dj-database-url, psycopg2-binary.

## Как задеплоить

1. Залейте код на GitHub (если ещё не залит).
2. Зайдите на [dashboard.render.com](https://dashboard.render.com) → **New** → **Blueprint**.
3. Подключите репозиторий (GitHub), выберите репозиторий с проектом.
4. Render подхватит **render.yaml** из корня: создаст PostgreSQL (plan: free) и Web Service (Python).
5. Нажмите **Apply**. Дождитесь окончания сборки и деплоя.
6. Сайт откроется по адресу вида `https://kvant.onrender.com`.

## После первого деплоя

БД после миграций пустая (нет страниц Wagtail). Выполните в **Render Shell** (в карточке сервиса → Shell):

```bash
# Суперпользователь (логин/пароль для /admin/)
python manage.py createsuperuser

# Разделы сайта: /novosti/, /o-nas/, /o-nas/sotrudniki/
python manage.py populate_site

# 7 квантумов с педагогами
python manage.py populate_quantums
```

Затем в админке **Wagtail** (**Settings** → **Sites**) отредактируйте запись сайта: в поле **Hostname** укажите ваш хост Render (например `kvant.onrender.com`) и сохраните.

## Переменные окружения

Задаются в **render.yaml** или в панели Render:

| Переменная | Откуда | Назначение |
|------------|--------|------------|
| `DATABASE_URL` | из БД (Blueprint) | Подключение к PostgreSQL |
| `SECRET_KEY` | generateValue | Секрет Django |
| `DJANGO_SETTINGS_MODULE` | `kvant_site.settings.production` | Продакшен-настройки |

При необходимости добавьте **ALLOWED_HOSTS** (через запятую) или **RENDER_EXTERNAL_URL** для Wagtail.

## Медиафайлы

На Render диск эфемерный — загруженные через админку файлы пропадут при следующем деплое. Для постоянного хранения позже можно подключить S3 или аналог.
