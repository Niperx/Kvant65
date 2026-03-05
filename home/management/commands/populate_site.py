"""
Management command: python manage.py populate_site

Создаёт все необходимые страницы в дереве Wagtail:
- /novosti/            NewsIndexPage
- /o-nas/              AboutPage
- /o-nas/sotrudniki/   EmployeesPage

Безопасно при повторном запуске — пропускает уже существующие страницы.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page


class Command(BaseCommand):
    help = "Создаёт страницы сайта в дереве Wagtail (новости, о нас, сотрудники)"

    def handle(self, *args, **options):
        from news.models import NewsIndexPage
        from about.models import AboutPage, EmployeesPage

        home = Page.objects.filter(slug="home", depth=2).first()
        if not home:
            self.stderr.write("Страница Home не найдена. Сначала выполните migrate.")
            return

        # 1. NewsIndexPage → /novosti/
        self._ensure_page(
            parent=home,
            model=NewsIndexPage,
            slug="novosti",
            title="Новости",
            extra={"intro": "<p>События, достижения и мероприятия РРЦ «Кванториум» Сахалин.</p>"},
        )

        # 2. AboutPage → /o-nas/
        about = self._ensure_page(
            parent=home,
            model=AboutPage,
            slug="o-nas",
            title="О нас",
            extra={"body": "<p>Региональный ресурсный центр дополнительного образования «Кванториум» Сахалинской области.</p>"},
        )

        # 3. EmployeesPage → /o-nas/sotrudniki/
        self._ensure_page(
            parent=about,
            model=EmployeesPage,
            slug="sotrudniki",
            title="Сотрудники",
            extra={"intro": "<p>Руководство и педагогический состав центра.</p>"},
        )

        self.stdout.write(self.style.SUCCESS("Готово! Структура сайта создана."))

    def _ensure_page(self, parent, model, slug, title, extra=None):
        """Создаёт страницу, если её нет. Возвращает экземпляр страницы."""
        existing = model.objects.filter(slug=slug).first()
        if existing:
            self.stdout.write(f"  Пропуск (уже есть): /{slug}/")
            return existing

        kwargs = {"title": title, "slug": slug, "live": True}
        if extra:
            kwargs.update(extra)

        page = model(**kwargs)
        parent.add_child(instance=page)
        self.stdout.write(f"  Создана: {page.full_url or '/' + slug + '/'}")
        return page
