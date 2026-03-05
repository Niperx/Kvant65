# Data migration: направления для мобильного комплекса, Голешова → Специалисты

from django.db import migrations


def set_mobile_directions_and_specialist(apps, schema_editor):
    EmployeePage = apps.get_model("about", "EmployeePage")
    # Голешова — в раздел «Специалисты»
    EmployeePage.objects.filter(slug="goleshova").update(department="specialist")

    # Направления мобильного комплекса (по данным с сайта)
    directions = {
        "sidorin": "VR/AR и IT",
        "yudin": "3D-моделирование",
        "vaulin": "VR/AR",
        "grishchenko": "АЭРО/ГЕО",
        "chernova": "Промышленный дизайн",
        "ganich": "Робототехника",
    }
    for slug, direction in directions.items():
        EmployeePage.objects.filter(slug=slug, department="mobile").update(direction=direction)


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("about", "0004_add_employee_direction_and_specialist"),
    ]

    operations = [
        migrations.RunPython(set_mobile_directions_and_specialist, noop),
    ]
