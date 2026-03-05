"""
Management command: python manage.py scrape_employee_bios

Парсит полные биографии с сайта:
  - Список: https://kvantorium.sakhalin.gov.ru/about-2/employees
  - Страница сотрудника: например /лисовский-даниил-денисович/ (кириллический slug)

Ссылки берутся только со страницы списка; из страницы сотрудника извлекается только
блок биографии (меню/навигация исключаются). Результат: about/data/scraped_bios.json.
Применить к БД: python manage.py update_employee_bios --from-scraped
Требует: pip install requests beautifulsoup4
"""
import json
import re
import time
from pathlib import Path
from urllib.parse import quote, unquote

from django.core.management.base import BaseCommand

# ФИО и slug из populate_employee_pages — для сопоставления со ссылками на сайте
EMPLOYEES_NAME_SLUG = [
    ("Ковач Александра Александровна", "kovach"),
    ("Худякова Полина Владимировна", "khudyakova"),
    ("Доля Екатерина Валерьевна", "dolya"),
    ("Гарифулин Денис Рафисович", "garifulin"),
    ("Чемякин Максим Вячеславович", "chemyakin"),
    ("Котова Оксана Сергеевна", "kotova"),
    ("Лисовский Даниил Денисович", "lisovskiy"),
    ("Попов Иван Александрович", "popov"),
    ("Москалева Галина Александровна", "moskaleva"),
    ("Максименко Анна Васильевна", "maksimenko"),
    ("Федотов Сергей Владимирович", "fedotov"),
    ("Ким Ен Чер", "kim-en-cher"),
    ("Васянин Алексей Александрович", "vasyanin"),
    ("Носова Анастасия Сергеевна", "nosova"),
    ("Суколенко Анастасия Витальевна", "sukolenko"),
    ("Носов Сергей Владимирович", "nosov"),
    ("Попкова Рената Аглямовна", "popkova"),
    ("Гладченко Ксения Сергеевна", "gladchenko"),
    ("Шкляева Виктория Енсиковна", "shklyaeva"),
    ("Голешова Александра Игоревна", "goleshova"),
    ("Ишкинина Вера Андреевна", "ishkinina"),
    ("Свириденко Анастасия Сергеевна", "sviridenko"),
    ("Хе Кен Ок", "khe-ken-ok"),
    ("Клягина Полина Евгеньевна", "klyagina"),
    ("Герасимов Антон Викторович", "gerasimov"),
    ("Ратушный Евгений Владимирович", "ratushnyy"),
    ("Сидорин Богдан Сергеевич", "sidorin"),
    ("Юдин Артём Сергеевич", "yudin"),
    ("Ваулин Илья Евгеньевич", "vaulin"),
    ("Грищенко Павел Алексеевич", "grishchenko"),
    ("Чернова Анастасия Евгеньевна", "chernova"),
    ("Ганич Максим Максимович", "ganich"),
]

BASE_URL = "https://kvantorium.sakhalin.gov.ru"
LIST_PATH = "/about-2/employees/"
REQUEST_TIMEOUT = 30
REQUEST_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
}
DELAY_BETWEEN_REQUESTS = 1.0

# Пути из меню сайта — блок с такими ссылками считаем навигацией
NAV_HREF_PATTERNS = re.compile(
    r"^/(about-2|novosti|kvantum|o-nas|sotrudniki|contacts?|raspisanie|vakansii)?/?$",
    re.I
)
MAX_LINKS_IN_BIO_BLOCK = 4
MIN_BIO_TEXT_LENGTH = 150

ALLOWED_TAGS = {"p", "ul", "ol", "li", "strong", "b", "em", "br", "a"}
ALLOWED_ATTRS = {"href"}


def normalize_name(s):
    """Для сопоставления ФИО: нижний регистр, нормальные пробелы."""
    return " ".join(s.lower().split()) if s else ""


def extract_bio_html(soup):
    """
    Извлекает блок с биографией. Исключаем навигацию: блоки с множеством ссылок
    на разделы сайта. Выбираем блок с максимумом текста (p, li) и минимумом ссылок.
    """
    from bs4 import BeautifulSoup

    def count_links(block):
        links = block.find_all("a", href=True)
        path = lambda a: (a.get("href") or "").split("?")[0]
        nav_like = sum(1 for a in links if NAV_HREF_PATTERNS.match(path(a)))
        return len(links), nav_like

    def text_length(block):
        return len(block.get_text(separator=" ", strip=True))

    def structure_score(block):
        p_count = len(block.find_all("p"))
        li_count = len(block.find_all("li"))
        link_count, nav_count = count_links(block)
        if link_count > MAX_LINKS_IN_BIO_BLOCK or nav_count >= 2:
            return -1
        return (p_count * 2 + li_count) - link_count * 2

    candidates = []
    for sel in [
        "div.block-rich_text",
        "div.rich-text",
        "[class*='stream']",
        "div.content",
        "article",
        "main",
    ]:
        for block in soup.select(sel):
            if block.find_parent("nav") or block.find_parent("header"):
                continue
            cls = block.get("class") or []
            if any(x in " ".join(cls).lower() for x in ("nav", "menu", "footer", "sidebar")):
                continue
            tlen = text_length(block)
            if tlen < MIN_BIO_TEXT_LENGTH:
                continue
            score = structure_score(block)
            if score >= 0:
                candidates.append((score, tlen, block))

    if not candidates:
        for tag in soup.find_all(["div", "section", "article"]):
            if tag.find_parent("nav"):
                continue
            tlen = text_length(tag)
            if tlen < MIN_BIO_TEXT_LENGTH or tlen > 100000:
                continue
            link_count, nav_like = count_links(tag)
            if link_count <= MAX_LINKS_IN_BIO_BLOCK and nav_like < 2:
                score = structure_score(tag)
                if score >= 0:
                    candidates.append((score, tlen, tag))

    if not candidates:
        return ""
    candidates.sort(key=lambda x: (-x[0], -x[1]))
    return sanitize_html(candidates[0][2])


def sanitize_html(element):
    """Оставляет только разрешённые теги."""
    from bs4 import BeautifulSoup
    html = element.decode_contents() if hasattr(element, "decode_contents") else str(element)
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all(True):
        if tag.name not in ALLOWED_TAGS:
            tag.unwrap()
    for tag in soup.find_all("a"):
        if not tag.get("href"):
            tag.unwrap()
    return soup.decode_contents().strip()


def fetch_url(session, path):
    """GET запрос с таймаутом и заголовками. path может содержать кириллицу — кодируем для URL."""
    path = path if path.startswith("/") else "/" + path
    url = BASE_URL + quote(path, safe="/")
    r = session.get(url, timeout=REQUEST_TIMEOUT, headers=REQUEST_HEADERS)
    r.raise_for_status()
    return r.text


def extract_employee_links_from_list(html):
    """
    Парсит страницу списка сотрудников. Ссылки на сотрудников ведут на страницы
    с кириллическим slug (например /лисовский-даниил-денисович/). Текст ссылки — ФИО.
    Сопоставляем ФИО с EMPLOYEES_NAME_SLUG и возвращаем список (наш_slug, url_path).
    """
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    # Собираем все ссылки, ведущие НЕ на разделы сайта (не /about-2/employees, не /novosti/ и т.д.)
    name_to_path = {}
    for a in soup.find_all("a", href=True):
        href = (a.get("href") or "").strip()
        if not href.startswith("/") or "?" in href:
            continue
        path = href.split("?")[0].rstrip("/")
        if not path:
            continue
        # Пропускаем ссылки на разделы (меню)
        if NAV_HREF_PATTERNS.match(path + "/") or path == "/about-2/employees":
            continue
        # Ссылка на страницу (одна или несколько частей пути, может быть кириллица)
        parts = path.strip("/").split("/")
        if not parts:
            continue
        # Считаем ссылкой на сотрудника: последний сегмент похож на ФИО (кириллица/дефисы)
        last = parts[-1]
        if re.search(r"[\u0400-\u04ff]", last) or re.match(r"^[a-z0-9-]+$", last):
            name_text = a.get_text(strip=True)
            if len(name_text) > 3 and len(name_text) < 120:
                name_to_path[normalize_name(name_text)] = path if path.startswith("/") else "/" + path

    # Сопоставляем с нашим списком по ФИО
    result = []
    used_paths = set()
    for name, slug in EMPLOYEES_NAME_SLUG:
        key = normalize_name(name)
        path = name_to_path.get(key)
        if path and path not in used_paths:
            result.append((slug, path))
            used_paths.add(path)
            continue
        # Попытка по фамилии (первое слово)
        surname = key.split()[0] if key else ""
        for n, p in name_to_path.items():
            if p in used_paths:
                continue
            if n.startswith(surname) or surname in n:
                result.append((slug, p))
                used_paths.add(p)
                break
    return result


class Command(BaseCommand):
    help = "Парсит полные биографии с kvantorium.sakhalin.gov.ru и сохраняет в about/data/scraped_bios.json"

    def add_arguments(self, parser):
        parser.add_argument(
            "--list-only",
            action="store_true",
            help="Только загрузить список сотрудников и вывести ссылки (не качать каждую страницу)",
        )
        parser.add_argument(
            "--delay",
            type=float,
            default=DELAY_BETWEEN_REQUESTS,
            help="Пауза между запросами в секундах (по умолчанию %s)" % DELAY_BETWEEN_REQUESTS,
        )

    def handle(self, *args, **options):
        try:
            import requests
            from bs4 import BeautifulSoup
        except ImportError:
            self.stderr.write("Установите зависимости: pip install requests beautifulsoup4")
            return

        data_dir = Path(__file__).resolve().parent.parent.parent / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        out_file = data_dir / "scraped_bios.json"

        session = requests.Session()
        delay = options["delay"]
        list_only = options["list_only"]

        # 1) Загружаем страницу списка и собираем ссылки на сотрудников
        self.stdout.write("Загрузка списка: %s%s" % (BASE_URL, LIST_PATH))
        try:
            list_html = fetch_url(session, LIST_PATH)
        except Exception as e:
            self.stderr.write(self.style.ERROR("Ошибка загрузки списка: %s" % e))
            return
        time.sleep(delay)

        employee_links = extract_employee_links_from_list(list_html)
        if employee_links:
            seen = set()
            unique = []
            for slug, path in employee_links:
                if slug not in seen:
                    seen.add(slug)
                    unique.append((slug, path))
            employee_links = unique
            self.stdout.write("Найдено по списку: %s ссылок (slug -> путь)" % len(employee_links))
        else:
            # Ссылок не сопоставили — пробуем типовой кириллический путь: /фамилия-имя-отчество/
            self.stdout.write("По списку не сопоставлено; пробуем пути вида /фамилия-имя-отчество/")
            employee_links = []
            for name, slug in EMPLOYEES_NAME_SLUG:
                path = "/" + "-".join(name.lower().split()) + "/"
                employee_links.append((slug, path))

        if list_only:
            for slug, path in employee_links:
                self.stdout.write("  %s -> %s" % (slug, path))
            return

        # 2) Для каждого сотрудника загружаем страницу и извлекаем биографию
        bios = {}
        for i, (slug, path) in enumerate(employee_links):
            self.stdout.write("[%s/%s] %s ..." % (i + 1, len(employee_links), slug))
            try:
                html = fetch_url(session, path)
                time.sleep(delay)
                soup = BeautifulSoup(html, "html.parser")
                bio = extract_bio_html(soup)
                if bio:
                    bios[slug] = bio
                    self.stdout.write("  OK, %s символов" % len(bio))
                else:
                    self.stdout.write(self.style.WARNING("  Контент не извлечён"))
            except Exception as e:
                self.stdout.write(self.style.ERROR("  Ошибка: %s" % e))

        # 3) Сохраняем в JSON
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(bios, f, ensure_ascii=False, indent=2)
        self.stdout.write(self.style.SUCCESS("\nСохранено в %s (%s записей)" % (out_file, len(bios))))
