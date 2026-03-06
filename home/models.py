from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.admin.panels import FieldPanel
from news.models import NewsPage
from quantums.models import QuantumPage


class HomePage(Page):
    search_auto_update = False
    hero_title = models.CharField(
        max_length=200,
        default="РРЦ «Кванториум»",
        verbose_name="Заголовок hero-блока",
    )
    hero_subtitle = models.CharField(
        max_length=400,
        default="Современная среда для ускоренного развития детей по научно-исследовательским и инженерно-техническим направлениям",
        verbose_name="Подзаголовок hero-блока",
    )
    intro_text = RichTextField(
        blank=True,
        verbose_name="Вступительный текст",
    )

    content_panels = Page.content_panels + [
        FieldPanel("hero_title"),
        FieldPanel("hero_subtitle"),
        FieldPanel("intro_text"),
    ]

    def get_context(self, request):
        context = super().get_context(request)
        context["quantums"] = QuantumPage.objects.live().order_by("title")
        context["latest_news"] = NewsPage.objects.live().order_by("-date")[:3]
        return context

    class Meta:
        verbose_name = "Главная страница"
