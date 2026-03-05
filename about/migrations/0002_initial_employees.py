"""
Data migration: создаёт начальный список сотрудников.
"""
from django.db import migrations


EMPLOYEES = [
    # Руководство
    {"name": "Ковач Александра Александровна", "role": "Директор", "department": "management", "sort_order": 0},
    {"name": "Худякова Полина Владимировна", "role": "Заместитель директора", "department": "management", "sort_order": 1},
    {"name": "Доля Екатерина Валерьевна", "role": "Заместитель директора", "department": "management", "sort_order": 2},
    # АЭРО
    {"name": "Гарифулин Денис Рафисович", "role": "Старший педагог доп. образования", "department": "aero", "sort_order": 0},
    {"name": "Чемякин Максим Вячеславович", "role": "Старший педагог доп. образования", "department": "aero", "sort_order": 1},
    # ХАЙТЕК
    {"name": "Федотов Сергей Владимирович", "role": "Старший педагог доп. образования", "department": "hitech", "sort_order": 0},
    # ЭНЕРДЖИ
    {"name": "Васянин Алексей Александрович", "role": "Старший педагог доп. образования", "department": "energy", "sort_order": 0},
    # ДИЗАЙН
    {"name": "Носова Анастасия Сергеевна", "role": "Старший педагог доп. образования", "department": "design", "sort_order": 0},
    {"name": "Суколенко Анастасия Витальевна", "role": "Старший педагог доп. образования", "department": "design", "sort_order": 1},
    # ПРОМРОБО
    {"name": "Попов Иван Александрович", "role": "Старший педагог доп. образования", "department": "robo", "sort_order": 0},
    {"name": "Москалева Галина Александровна", "role": "Старший педагог доп. образования", "department": "robo", "sort_order": 1},
    {"name": "Максименко Анна Васильевна", "role": "Старший педагог доп. образования", "department": "robo", "sort_order": 2},
    # АЙТИ
    {"name": "Котова Оксана Сергеевна", "role": "Старший педагог доп. образования", "department": "it", "sort_order": 0},
    {"name": "Лисовский Даниил Денисович", "role": "Старший педагог доп. образования", "department": "it", "sort_order": 1},
    # VR/AR
    {"name": "Ким Ен Чер", "role": "Старший педагог доп. образования", "department": "vrar", "sort_order": 0},
]


def create_employees(apps, schema_editor):
    Employee = apps.get_model("about", "Employee")
    for data in EMPLOYEES:
        Employee.objects.create(**data)


def delete_employees(apps, schema_editor):
    Employee = apps.get_model("about", "Employee")
    Employee.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ("about", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_employees, delete_employees),
    ]
