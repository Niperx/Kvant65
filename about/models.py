from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from wagtail.snippets.models import register_snippet


DEPARTMENT_CHOICES = [
    ("management", "Руководство"),
    ("aero", "АЭРО"),
    ("it", "АЙТИ"),
    ("robo", "ПРОМРОБО"),
    ("hitech", "ХАЙТЕК"),
    ("vrar", "VR/AR"),
    ("energy", "ЭНЕРДЖИ"),
    ("design", "ПРОМДИЗАЙН"),
    ("media", "Медиа"),
    ("mobile", "Мобильный комплекс"),
    ("methodist", "Методисты"),
    ("specialist", "Специалисты"),
    ("organizer", "Педагоги-организаторы"),
    ("engineer", "Инженеры"),
    ("other", "Прочее"),
]

# Порядок на странице: руководство → пед. состав (квантумы + мобильный) → методисты → специалисты → орг. → инженеры
DEPARTMENT_ORDER = [
    "management", "aero", "it", "robo", "hitech", "vrar", "energy", "design",
    "media", "mobile", "methodist", "specialist", "organizer", "engineer", "other",
]


@register_snippet
class Employee(models.Model):
    DEPARTMENT_CHOICES = DEPARTMENT_CHOICES

    name = models.CharField(max_length=200, verbose_name="ФИО")
    role = models.CharField(max_length=200, verbose_name="Должность")
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default="other",
        verbose_name="Отдел/Квантум",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Фото",
    )
    bio = RichTextField(blank=True, verbose_name="О сотруднике")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    panels = [
        FieldPanel("name"),
        FieldPanel("role"),
        FieldPanel("department"),
        FieldPanel("photo"),
        FieldPanel("bio"),
        FieldPanel("sort_order"),
    ]

    class Meta:
        verbose_name = "Сотрудник (устаревшее)"
        verbose_name_plural = "Сотрудники (устаревшее)"
        ordering = ["sort_order", "name"]

    def __str__(self):
        return self.name


class EmployeePage(Page):
    """Страница-профиль отдельного сотрудника."""
    search_auto_update = False

    role = models.CharField(max_length=200, verbose_name="Должность")
    department = models.CharField(
        max_length=20,
        choices=DEPARTMENT_CHOICES,
        default="other",
        verbose_name="Отдел/Квантум",
    )
    direction = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Направление (для мобильного комплекса)",
        help_text="Например: 3D-моделирование, VR/AR, АЭРО/ГЕО. Отображается под должностью.",
    )
    photo = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Фото",
    )
    bio = RichTextField(blank=True, verbose_name="О сотруднике")

    content_panels = Page.content_panels + [
        FieldPanel("role"),
        FieldPanel("department"),
        FieldPanel("direction"),
        FieldPanel("photo"),
        FieldPanel("bio"),
    ]

    parent_page_types = ["about.EmployeesPage"]
    subpage_types = []

    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"

    def get_department_label(self):
        return dict(DEPARTMENT_CHOICES).get(self.department, self.department)


class EmployeesPage(Page):
    search_auto_update = False
    intro = RichTextField(blank=True, verbose_name="Вступление")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = ["about.EmployeePage"]

    class Meta:
        verbose_name = "Страница сотрудников"

    def get_context(self, request):
        context = super().get_context(request)
        employees = EmployeePage.objects.live().child_of(self)
        dept_labels = dict(DEPARTMENT_CHOICES)

        context["management"] = employees.filter(department="management").order_by("title")

        # Педагогический состав: квантумы (АЭРО, АЙТИ, … Медиа)
        teacher_depts = ["aero", "it", "robo", "hitech", "vrar", "energy", "design", "media"]
        context["teachers_by_dept"] = [
            {
                "key": dept,
                "label": dept_labels.get(dept, dept),
                "employees": employees.filter(department=dept).order_by("title"),
            }
            for dept in teacher_depts
            if employees.filter(department=dept).exists()
        ]

        # Мобильный комплекс: группировка по полю «Направление»
        mobile_qs = employees.filter(department="mobile").order_by("direction", "title")
        mobile_by_dir = {}
        for emp in mobile_qs:
            key = (emp.direction or "Без направления").strip()
            if key not in mobile_by_dir:
                mobile_by_dir[key] = []
            mobile_by_dir[key].append(emp)
        context["mobile_by_direction"] = [
            {"direction": d, "employees": mobile_by_dir[d]}
            for d in sorted(mobile_by_dir.keys(), key=lambda x: (x == "Без направления", x))
        ]

        context["methodists"] = employees.filter(department="methodist").order_by("title")
        context["specialists"] = employees.filter(department="specialist").order_by("title")
        context["organizers"] = employees.filter(department="organizer").order_by("title")
        context["engineers"] = employees.filter(department="engineer").order_by("title")
        return context


class AboutPage(Page):
    """Универсальная текстовая страница: О центре, Документы, Мобильный комплекс и т.д."""
    search_auto_update = False
    body = RichTextField(blank=True, verbose_name="Текст страницы")

    content_panels = Page.content_panels + [
        FieldPanel("body"),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = ["about.EmployeesPage", "about.AboutPage"]

    class Meta:
        verbose_name = "О нас (текстовая страница)"
        verbose_name_plural = "О нас (текстовые страницы)"


class SchedulePage(Page):
    """Страница «Расписание занятий» с таблицей."""
    search_auto_update = False
    intro = RichTextField(blank=True, verbose_name="Вступление")
    body = RichTextField(blank=True, verbose_name="Таблица расписания (редактор)")
    schedule_table_html = models.TextField(
        blank=True,
        verbose_name="Таблица расписания (HTML)",
        help_text="Вставка готовой HTML-таблицы. Если задано — выводится вместо поля выше.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("schedule_table_html"),
    ]

    parent_page_types = ["wagtailcore.Page"]
    subpage_types = []

    class Meta:
        verbose_name = "Расписание занятий"
        verbose_name_plural = "Расписание занятий"
