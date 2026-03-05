"""
Management command: python manage.py populate_employee_pages

Создаёт страницы сотрудников (EmployeePage) внутри /o-nas/sotrudniki/.
Безопасно при повторном запуске — пропускает уже существующие по slug.

Включает всех сотрудников с оригинального сайта kvantorium.sakhalin.gov.ru
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify


EMPLOYEES = [
    # ── Руководство ──────────────────────────────────────────────────────────
    {"name": "Ковач Александра Александровна",  "role": "Директор",                             "dept": "management", "slug": "kovach"},
    {"name": "Худякова Полина Владимировна",    "role": "Заместитель директора",                 "dept": "management", "slug": "khudyakova"},
    {"name": "Доля Екатерина Валерьевна",       "role": "Заместитель директора",                 "dept": "management", "slug": "dolya"},

    # ── АЭРО ─────────────────────────────────────────────────────────────────
    {"name": "Гарифулин Денис Рафисович",       "role": "Старший педагог доп. образования",      "dept": "aero",       "slug": "garifulin"},
    {"name": "Чемякин Максим Вячеславович",     "role": "Старший педагог доп. образования",      "dept": "aero",       "slug": "chemyakin"},

    # ── АЙТИ ─────────────────────────────────────────────────────────────────
    {"name": "Котова Оксана Сергеевна",         "role": "Старший педагог доп. образования",      "dept": "it",         "slug": "kotova"},
    {"name": "Лисовский Даниил Денисович",      "role": "Старший педагог доп. образования",      "dept": "it",         "slug": "lisovskiy"},

    # ── ПРОМРОБО ─────────────────────────────────────────────────────────────
    {"name": "Попов Иван Александрович",        "role": "Старший педагог доп. образования",      "dept": "robo",       "slug": "popov"},
    {"name": "Москалева Галина Александровна",  "role": "Старший педагог доп. образования",      "dept": "robo",       "slug": "moskaleva"},
    {"name": "Максименко Анна Васильевна",      "role": "Старший педагог доп. образования",      "dept": "robo",       "slug": "maksimenko"},

    # ── ХАЙТЕК ───────────────────────────────────────────────────────────────
    {"name": "Федотов Сергей Владимирович",     "role": "Старший педагог доп. образования",      "dept": "hitech",     "slug": "fedotov"},

    # ── VR/AR ─────────────────────────────────────────────────────────────────
    {"name": "Ким Ен Чер",                      "role": "Старший педагог доп. образования",      "dept": "vrar",       "slug": "kim-en-cher"},

    # ── ЭНЕРДЖИ ──────────────────────────────────────────────────────────────
    {"name": "Васянин Алексей Александрович",   "role": "Старший педагог доп. образования",      "dept": "energy",     "slug": "vasyanin"},

    # ── ПРОМДИЗАЙН ───────────────────────────────────────────────────────────
    {"name": "Носова Анастасия Сергеевна",      "role": "Старший педагог доп. образования",      "dept": "design",     "slug": "nosova"},
    {"name": "Суколенко Анастасия Витальевна",  "role": "Старший педагог доп. образования",      "dept": "design",     "slug": "sukolenko"},

    # ── Медиа ────────────────────────────────────────────────────────────────
    {"name": "Носов Сергей Владимирович",       "role": "Старший педагог доп. образования",      "dept": "media",      "slug": "nosov"},

    # ── Методисты ────────────────────────────────────────────────────────────
    {"name": "Попкова Рената Аглямовна",        "role": "Методист",                              "dept": "methodist",  "slug": "popkova"},
    {"name": "Гладченко Ксения Сергеевна",      "role": "Методист",                              "dept": "methodist",  "slug": "gladchenko"},
    {"name": "Шкляева Виктория Енсиковна",      "role": "Методист",                              "dept": "methodist",  "slug": "shklyaeva"},
    {"name": "Голешова Александра Игоревна",    "role": "Специалист по УМР",                     "dept": "methodist",  "slug": "goleshova"},

    # ── Педагоги-организаторы ────────────────────────────────────────────────
    {"name": "Ишкинина Вера Андреевна",         "role": "Педагог-организатор",                   "dept": "organizer",  "slug": "ishkinina"},
    {"name": "Свириденко Анастасия Сергеевна",  "role": "Педагог-организатор",                   "dept": "organizer",  "slug": "sviridenko"},
    {"name": "Хе Кен Ок",                       "role": "Педагог-организатор",                   "dept": "organizer",  "slug": "khe-ken-ok"},

    # ── Инженеры ─────────────────────────────────────────────────────────────
    {"name": "Клягина Полина Евгеньевна",       "role": "Инженер",                               "dept": "engineer",   "slug": "klyagina"},
    {"name": "Герасимов Антон Викторович",      "role": "Инженер",                               "dept": "engineer",   "slug": "gerasimov"},
    {"name": "Ратушный Евгений Владимирович",   "role": "Инженер",                               "dept": "engineer",   "slug": "ratushnyy"},

    # ── Мобильный комплекс ───────────────────────────────────────────────────
    {"name": "Сидорин Богдан Сергеевич",        "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "sidorin"},
    {"name": "Юдин Артём Сергеевич",            "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "yudin"},
    {"name": "Ваулин Илья Евгеньевич",          "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "vaulin"},
    {"name": "Грищенко Павел Алексеевич",       "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "grishchenko"},
    {"name": "Чернова Анастасия Евгеньевна",    "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "chernova"},
    {"name": "Ганич Максим Максимович",         "role": "Педагог мобильного комплекса",          "dept": "mobile",     "slug": "ganich"},
]


class Command(BaseCommand):
    help = "Создаёт страницы сотрудников в Wagtail (EmployeePage)"

    def handle(self, *args, **options):
        from about.models import EmployeePage, EmployeesPage

        parent = EmployeesPage.objects.filter(slug="sotrudniki").first()
        if not parent:
            self.stderr.write("EmployeesPage (slug=sotrudniki) не найдена. Запустите сначала populate_site.")
            return

        created = 0
        skipped = 0

        for data in EMPLOYEES:
            if EmployeePage.objects.filter(slug=data["slug"]).exists():
                skipped += 1
                continue

            page = EmployeePage(
                title=data["name"],
                slug=data["slug"],
                role=data["role"],
                department=data["dept"],
                live=True,
            )
            parent.add_child(instance=page)
            created += 1
            self.stdout.write(f"  + {data['name']}")

        self.stdout.write(self.style.SUCCESS(
            f"\nГотово: создано {created}, пропущено {skipped} (уже есть)."
        ))
