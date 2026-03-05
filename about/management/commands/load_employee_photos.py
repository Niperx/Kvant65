"""
Management command: python manage.py load_employee_photos

Загружает фотографии сотрудников из папки media/employee_photos/
и привязывает их к соответствующим EmployeePage.

Соглашение по именованию файлов:
  Имя файла (без расширения) = slug сотрудника.
  Примеры:
    kovach.jpg         → /o-nas/sotrudniki/kovach/
    garifulin.jpg      → /o-nas/sotrudniki/garifulin/
    kim-en-cher.jpg    → /o-nas/sotrudniki/kim-en-cher/

Поддерживаемые форматы: .jpg, .jpeg, .png, .webp

Запуск:
  python manage.py load_employee_photos

Повторный запуск безопасен: обновляет фото если оно уже есть,
или пропускает если файл не изменился (по имени файла в Wagtail Images).
"""
import os
from pathlib import Path

from django.core.files.images import ImageFile
from django.core.management.base import BaseCommand

from wagtail.images.models import Image as WagtailImage

PHOTOS_DIR = Path("media") / "employee_photos"
SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


class Command(BaseCommand):
    help = "Загружает фото сотрудников из media/employee_photos/ и привязывает к EmployeePage"

    def handle(self, *args, **options):
        from about.models import EmployeePage

        if not PHOTOS_DIR.exists():
            self.stderr.write(
                f"Папка {PHOTOS_DIR} не найдена.\n"
                "Создайте её и положите фотографии: media/employee_photos/kovach.jpg и т.д."
            )
            return

        photo_files = [
            f for f in PHOTOS_DIR.iterdir()
            if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
        ]

        if not photo_files:
            self.stdout.write(f"В папке {PHOTOS_DIR} нет фотографий.")
            return

        loaded = 0
        not_found = []

        for photo_path in sorted(photo_files):
            slug = photo_path.stem  # filename without extension
            employee = EmployeePage.objects.filter(slug=slug).first()

            if not employee:
                not_found.append(photo_path.name)
                continue

            # Загружаем в Wagtail Images (или находим существующее по заголовку)
            title = f"photo_{slug}"
            wagtail_img = WagtailImage.objects.filter(title=title).first()

            if wagtail_img:
                # Обновляем файл
                with open(photo_path, "rb") as f:
                    wagtail_img.file = ImageFile(f, name=photo_path.name)
                    wagtail_img.save()
            else:
                with open(photo_path, "rb") as f:
                    wagtail_img = WagtailImage(title=title)
                    wagtail_img.file = ImageFile(f, name=photo_path.name)
                    wagtail_img.save()

            employee.photo = wagtail_img
            employee.save()
            loaded += 1
            self.stdout.write(f"  ✓ {employee.title} ← {photo_path.name}")

        self.stdout.write(self.style.SUCCESS(f"\nЗагружено фото: {loaded}"))

        if not_found:
            self.stdout.write(self.style.WARNING(
                "\nФайлы без совпадения (slug сотрудника не найден):"
            ))
            for name in not_found:
                self.stdout.write(f"  ? {name}")
            self.stdout.write(
                "\nПроверьте: имя файла (без расширения) должно совпадать со slug сотрудника.\n"
                "Список slug: python manage.py shell -c "
                "\"from about.models import EmployeePage; "
                "[print(p.slug, '←', p.title) for p in EmployeePage.objects.all()]\""
            )
