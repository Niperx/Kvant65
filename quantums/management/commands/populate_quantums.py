"""
Management command: python manage.py populate_quantums

Создаёт раздел «Квантумы» с 7 направлениями и педагогами.
Безопасно запускать повторно — пропустит если данные уже есть.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page


QUANTUMS_DATA = [
    {
        "title": "АЭРО",
        "slug": "aero",
        "icon_emoji": "✈️",
        "accent_color": "#6366f1",
        "short_description": "Сборка и программирование квадрокоптеров, основы аэродинамики и пилотирование дронов.",
        "body": "<p>Направление АЭРО посвящено беспилотным авиационным системам. Участники изучают сборку шасси квадрокоптеров, электронику, подключение питания и калибровку оборудования, а также программирование полётных контроллеров и практическое пилотирование.</p><p>Занятия проходят в формате практических проектов с элементами соревновательной деятельности.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Гарифулин Денис Рафисович", "Старший педагог доп. образования"),
            ("Чемякин Максим Вячеславович", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "АЙТИ",
        "slug": "it",
        "icon_emoji": "💻",
        "accent_color": "#0ea5e9",
        "short_description": "Программирование на Python, C++, веб-разработка, алгоритмы и создание цифровых продуктов.",
        "body": "<p>IT-квантум обучает созданию цифровых продуктов. Программа охватывает вычислительное мышление, Scratch, Python, C++, основы веб (HTML, CSS, JavaScript), алгоритмы и работу в IDE.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Котова Оксана Сергеевна", "Старший педагог доп. образования"),
            ("Лисовский Даниил Денисович", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "ПРОМРОБО",
        "slug": "robo",
        "icon_emoji": "🤖",
        "accent_color": "#f59e0b",
        "short_description": "Промышленная робототехника: проектирование, программирование роботов и автоматизация производства.",
        "body": "<p>Промышленная робототехника — направление для тех, кто хочет создавать автоматические производственные системы. Участники работают с платформами Lego EV3, Arduino, Studica Robotics, ТРИК.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Попов Иван Александрович", "Старший педагог доп. образования"),
            ("Москалева Галина Александровна", "Старший педагог доп. образования"),
            ("Максименко Анна Васильевна", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "ХАЙТЕК",
        "slug": "hitech",
        "icon_emoji": "⚙️",
        "accent_color": "#10b981",
        "short_description": "Высокотехнологичная лаборатория: 3D-печать, лазерная резка, ЧПУ-станки и прототипирование.",
        "body": "<p>Хайтек-лаборатория оснащена 3D-принтерами, лазерными станками и ЧПУ-оборудованием. Участники осваивают теорию решения изобретательских задач, работу с электроникой, пайку и основы технологического предпринимательства.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Федотов Сергей Владимирович", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "VR/AR",
        "slug": "vrar",
        "icon_emoji": "🥽",
        "accent_color": "#8b5cf6",
        "short_description": "Разработка приложений и игр в виртуальной и дополненной реальности на Unity и C#.",
        "body": "<p>VR/AR-квантум переводит участников из пользователей технологий в их создателей. Программа включает основы 3D-моделирования, программирование на C# и разработку на Unity.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Ким Ен Чер", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "ЭНЕРДЖИ",
        "slug": "energy",
        "icon_emoji": "⚡",
        "accent_color": "#f97316",
        "short_description": "Альтернативная энергетика: солнечные батареи, ветрогенераторы, водородные элементы и экосистемы.",
        "body": "<p>Энерджиквантум изучает возобновляемые источники энергии: солнечную, ветровую, гидро- и водородную. Участники строят реальные энергетические системы и проектируют экологичные решения.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Васянин Алексей Александрович", "Старший педагог доп. образования"),
        ],
    },
    {
        "title": "ПРОМДИЗАЙН",
        "slug": "design",
        "icon_emoji": "🎨",
        "accent_color": "#ec4899",
        "short_description": "Промышленный дизайн: проектирование изделий, 3D-моделирование и создание прототипов.",
        "body": "<p>Промдизайнквантум обучает созданию функциональных и эстетичных промышленных изделий. Участники осваивают принципы дизайна, компьютерное моделирование и прототипирование.</p>",
        "age_range": "7–17 лет",
        "max_students": 12,
        "teachers": [
            ("Носова Анастасия Сергеевна", "Старший педагог доп. образования"),
            ("Суколенко Анастасия Витальевна", "Старший педагог доп. образования"),
        ],
    },
]


class Command(BaseCommand):
    help = "Создаёт начальный контент: раздел Квантумы с 7 направлениями"

    def handle(self, *args, **options):
        from quantums.models import QuantumIndexPage, QuantumPage, QuantumTeacher

        # Find home page
        home_page = Page.objects.filter(depth=2).first()
        if not home_page:
            self.stderr.write("Home page not found. Run migrate first.")
            return

        # Check if already exists
        if QuantumIndexPage.objects.filter(slug="kvantum").exists():
            self.stdout.write(self.style.WARNING("QuantumIndexPage already exists. Skipping."))
            return

        # Create index page
        qi = QuantumIndexPage(
            title="Квантумы",
            slug="kvantum",
            intro="<p>Выберите направление — все программы бесплатны по сертификату дополнительного образования.</p>",
            live=True,
        )
        home_page.add_child(instance=qi)
        self.stdout.write(f"  Created: {qi.title}")

        for data in QUANTUMS_DATA:
            qp = QuantumPage(
                title=data["title"],
                slug=data["slug"],
                icon_emoji=data["icon_emoji"],
                accent_color=data["accent_color"],
                short_description=data["short_description"],
                body=data["body"],
                age_range=data["age_range"],
                max_students=data["max_students"],
                live=True,
            )
            qi.add_child(instance=qp)

            for order, (name, role) in enumerate(data["teachers"]):
                QuantumTeacher.objects.create(
                    page=qp,
                    name=name,
                    role=role,
                    sort_order=order,
                )

            self.stdout.write(f"    + {qp.title} ({len(data['teachers'])} педагогов)")

        self.stdout.write(self.style.SUCCESS("Done! Создано 7 квантумов."))
