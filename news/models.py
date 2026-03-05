from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField
from wagtail.images.models import Image
from wagtail.admin.panels import FieldPanel
from wagtail.search import index


class NewsIndexPage(Page):
    search_auto_update = False
    intro = RichTextField(blank=True, verbose_name="Вступление")

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    subpage_types = ["news.NewsPage"]

    class Meta:
        verbose_name = "Лента новостей"

    def get_template(self, request, *args, **kwargs):
        # Отдаём фрагмент списка только когда запрос — смена фильтра (цель #news-list-wrap).
        # Переход по ссылке «Новости» в меню (цель #main-content) получает полную страницу.
        if request.headers.get("HX-Request") and request.headers.get("HX-Target") == "news-list-wrap":
            return "news/news_list_partial.html"
        return super().get_template(request, *args, **kwargs)

    def get_context(self, request):
        context = super().get_context(request)
        category = request.GET.get("category", "")
        news_qs = NewsPage.objects.live().child_of(self).order_by("-date")
        if category:
            news_qs = news_qs.filter(category=category)
        context["news_list"] = news_qs
        context["current_category"] = category
        return context


class NewsPage(Page):
    search_auto_update = False
    CATEGORY_CHOICES = [
        ("news", "Новость"),
        ("event", "Мероприятие"),
        ("achievement", "Достижение"),
    ]

    date = models.DateField(verbose_name="Дата публикации")
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default="news",
        verbose_name="Категория",
    )
    cover_image = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name="Обложка",
    )
    intro = models.CharField(
        max_length=500,
        verbose_name="Краткое описание",
    )
    body = RichTextField(verbose_name="Текст статьи")

    search_fields = Page.search_fields + [
        index.SearchField("intro"),
        index.SearchField("body"),
    ]

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("category"),
        FieldPanel("cover_image"),
        FieldPanel("intro"),
        FieldPanel("body"),
    ]

    parent_page_types = ["news.NewsIndexPage"]

    class Meta:
        verbose_name = "Новость / Мероприятие"
        verbose_name_plural = "Новости и мероприятия"

    def get_category_display_name(self):
        return dict(self.CATEGORY_CHOICES).get(self.category, self.category)
