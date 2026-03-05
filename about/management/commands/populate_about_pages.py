"""
Создаёт страницы «Основные сведения», «Документы», «Мобильный комплекс», «Расписание»
и заполняет их контентом из about/data/*.html.

Запуск: python manage.py populate_about_pages

Требует выполненный populate_site (страница «О нас» slug=o-nas и home).
Безопасно при повторном запуске — обновляет контент существующих страниц, если передать --update.
"""
import os
from django.core.management.base import BaseCommand
from wagtail.models import Page

from about.models import AboutPage, SchedulePage


def _read_data_file(path_relative_to_app, strip_comment=True):
    """Читает файл из about/data/, убирает первую строку-комментарий при strip_comment=True."""
    app_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(app_dir, "data", path_relative_to_app)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    if strip_comment and content.lstrip().startswith("<!--"):
        end = content.find("-->")
        if end != -1:
            content = content[end + 3 :].lstrip()
    return content


class Command(BaseCommand):
    help = "Создаёт страницы О центре, Документы, Мобильный комплекс, Расписание с контентом из about/data/"

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Обновить body/schedule_table_html у уже существующих страниц из файлов data/",
        )

    def handle(self, *args, **options):
        home = Page.objects.filter(slug="home", depth=2).first()
        if not home:
            self.stderr.write(self.style.ERROR("Страница Home не найдена. Сначала выполните migrate и populate_site."))
            return

        o_nas = AboutPage.objects.filter(slug="o-nas").first()
        if not o_nas:
            self.stderr.write(self.style.ERROR("Страница «О нас» (slug=o-nas) не найдена. Выполните python manage.py populate_site."))
            return

        update = options.get("update", False)

        # 1. Основные сведения (О центре) — дочерняя к «О нас»
        body_osn = _read_data_file("osnovnye_svedeniya_body.html")
        if body_osn is None:
            self.stderr.write(self.style.WARNING("Файл about/data/osnovnye_svedeniya_body.html не найден."))
        else:
            page, created = self._ensure_about_page(
                parent=o_nas,
                slug="osnovnye-svedeniya",
                title="Основные сведения",
                body=body_osn,
                update=update,
            )
            self.stdout.write(f"  {'Создана' if created else 'Обновлена'}: {page.url_path} — Основные сведения")

        # 2. Документы — заглушка
        body_doc = "<p>Раздел «Документы». Добавьте ссылки на документы через редактор страницы или загрузите файлы в раздел «Документы» админки.</p>"
        page, created = self._ensure_about_page(
            parent=o_nas,
            slug="dokumenty",
            title="Документы",
            body=body_doc,
            update=update,
        )
        self.stdout.write(f"  {'Создана' if created else 'Обновлена'}: {page.url_path} — Документы")

        # 3. Мобильный комплекс
        body_mob = _read_data_file("mobilnyy_kompleks_body.html")
        if body_mob is None:
            self.stderr.write(self.style.WARNING("Файл about/data/mobilnyy_kompleks_body.html не найден."))
            body_mob = "<p>Мобильный комплекс РРЦ «Кванториум».</p>"
        page, created = self._ensure_about_page(
            parent=o_nas,
            slug="mobilnyy-kompleks",
            title="Мобильный комплекс",
            body=body_mob,
            update=update,
        )
        self.stdout.write(f"  {'Создана' if created else 'Обновлена'}: {page.url_path} — Мобильный комплекс")

        # 4. Расписание — дочерняя к home
        table_html = _read_data_file("raspisanie_table.html")
        if table_html is None:
            self.stderr.write(self.style.WARNING("Файл about/data/raspisanie_table.html не найден."))
            table_html = ""
        intro_schedule = "<p><strong>Актуальное расписание занятий на 2025–2026 учебный год.</strong></p>"
        page, created = self._ensure_schedule_page(
            parent=home,
            slug="raspisanie",
            title="Расписание занятий",
            intro=intro_schedule,
            schedule_table_html=table_html,
            update=update,
        )
        self.stdout.write(f"  {'Создана' if created else 'Обновлена'}: {page.url_path} — Расписание занятий")

        self.stdout.write(self.style.SUCCESS("Готово. Страницы созданы/обновлены."))

    def _ensure_about_page(self, parent, slug, title, body, update=False):
        existing = AboutPage.objects.child_of(parent).filter(slug=slug).first()
        if existing:
            if update and body:
                existing.body = body
                existing.save_revision().publish()
            return existing, False
        page = AboutPage(title=title, slug=slug, body=body, live=True)
        parent.add_child(instance=page)
        return page, True

    def _ensure_schedule_page(self, parent, slug, title, intro="", schedule_table_html="", update=False):
        existing = SchedulePage.objects.child_of(parent).filter(slug=slug).first()
        if existing:
            if update:
                if intro:
                    existing.intro = intro
                if schedule_table_html is not None:
                    existing.schedule_table_html = schedule_table_html
                existing.save_revision().publish()
            return existing, False
        page = SchedulePage(
            title=title,
            slug=slug,
            intro=intro,
            schedule_table_html=schedule_table_html or "",
            live=True,
        )
        parent.add_child(instance=page)
        return page, True
