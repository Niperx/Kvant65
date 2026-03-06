from django.db import models
from modelcluster.fields import ParentalKey
from wagtail.models import Page, Orderable
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel, InlinePanel


class QuantumIndexPage(Page):
    search_auto_update = False
    intro = RichTextField(blank=True, verbose_name="Вступление")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = ["quantums.QuantumPage"]

    class Meta:
        verbose_name = "Раздел «Квантумы»"

    def get_context(self, request):
        context = super().get_context(request)
        context["quantums"] = QuantumPage.objects.live().child_of(self).order_by("title")
        return context


class QuantumTeacher(Orderable):
    page = ParentalKey("QuantumPage", on_delete=models.CASCADE, related_name="teachers")
    name = models.CharField(max_length=200, verbose_name="ФИО")
    role = models.CharField(
        max_length=200,
        default="Старший педагог доп. образования",
        verbose_name="Должность",
    )

    panels = [
        FieldPanel("name"),
        FieldPanel("role"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Педагог"


class QuantumGalleryImage(Orderable):
    page = ParentalKey("QuantumPage", on_delete=models.CASCADE, related_name="gallery_images")
    image = models.ForeignKey(
        "wagtailimages.Image",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name="Фото",
    )
    caption = models.CharField(max_length=200, blank=True, verbose_name="Подпись")

    panels = [
        FieldPanel("image"),
        FieldPanel("caption"),
    ]

    class Meta(Orderable.Meta):
        verbose_name = "Фото галереи"


class QuantumPage(Page):
    search_auto_update = False
    QUANTUM_COLORS = [
        ("#6366f1", "Индиго"),
        ("#0ea5e9", "Голубой"),
        ("#f59e0b", "Янтарный"),
        ("#10b981", "Зелёный"),
        ("#8b5cf6", "Фиолетовый"),
        ("#f97316", "Оранжевый"),
        ("#ec4899", "Розовый"),
    ]

    short_description = models.CharField(
        max_length=300,
        verbose_name="Краткое описание (для карточки)",
    )
    age_range = models.CharField(
        max_length=20,
        default="7–17 лет",
        verbose_name="Возрастной диапазон",
    )
    max_students = models.PositiveIntegerField(
        default=12,
        verbose_name="Макс. учеников в группе",
    )
    accent_color = models.CharField(
        max_length=7,
        default="#6366f1",
        choices=QUANTUM_COLORS,
        verbose_name="Цвет акцента",
    )
    icon_emoji = models.CharField(
        max_length=4,
        default="🔬",
        verbose_name="Иконка (emoji)",
        help_text="Emoji для карточки квантума",
    )
    body = RichTextField(blank=True, verbose_name="Описание программы")

    content_panels = Page.content_panels + [
        FieldPanel("icon_emoji"),
        FieldPanel("short_description"),
        FieldPanel("accent_color"),
        FieldPanel("age_range"),
        FieldPanel("max_students"),
        FieldPanel("body"),
        InlinePanel("teachers", label="Педагоги"),
        InlinePanel("gallery_images", label="Галерея фото"),
    ]

    parent_page_types = ["quantums.QuantumIndexPage"]

    def get_context(self, request):
        context = super().get_context(request)
        from about.models import EmployeePage
        teachers_with_employee = []
        for teacher in self.teachers.all():
            emp = EmployeePage.objects.live().filter(title__iexact=teacher.name.strip()).first() if teacher.name else None
            teachers_with_employee.append({"teacher": teacher, "employee_page": emp})
        context["teachers_with_employee"] = teachers_with_employee
        return context

    class Meta:
        verbose_name = "Квантум"
        verbose_name_plural = "Квантумы"
