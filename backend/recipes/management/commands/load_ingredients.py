import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from recipes.models import Ingredient

CSV_PATH = Path("/app/data/ingredients.csv")
ENCODINGS = ["utf-8-sig", "utf-8", "cp1251", "windows-1251", "iso-8859-1"]


class Command(BaseCommand):
    help = (
        "Загружает ингредиенты из /app/data/ingredients.csv "
        "(формат: name,measurement_unit)"
    )

    def handle(self, *args, **options):
        if not CSV_PATH.exists():
            self.stdout.write(self.style.ERROR(f"Файл не найден: {CSV_PATH}"))
            return

        self.stdout.write(f"Загрузка ингредиентов из: {CSV_PATH}")

        rows = self._read_csv_with_fallback(CSV_PATH)
        if rows is None:
            self.stdout.write(
                self.style.ERROR(
                    "Не удалось прочитать CSV ни в одной из кодировок."
                )
            )
            return

        items = []
        for row in rows:
            if not row or len(row) < 2:
                continue
            name = (row[0] or "").strip()
            measurement_unit = (row[1] or "").strip()
            if not name or not measurement_unit:
                continue
            # Пропуск заголовка, если есть
            if name.lower() == "name" and measurement_unit.lower() in {
                "unit",
                "measurement_unit",
                "единица",
            }:
                continue
            items.append(
                Ingredient(name=name, measurement_unit=measurement_unit)
            )

        if not items:
            self.stdout.write(
                self.style.WARNING(
                    "CSV файл пуст или не содержит валидных строк."
                )
            )
            return

        created = Ingredient.objects.bulk_create(items, ignore_conflicts=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"Успешно обработано строк: {len(items)}, "
                f"создано записей: {len(created)}"
            )
        )

    def _read_csv_with_fallback(self, path: Path):
        for enc in ENCODINGS:
            try:
                with path.open("r", encoding=enc, newline="") as f:
                    reader = csv.reader(f)
                    return list(reader)
            except UnicodeDecodeError:
                continue
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Проблема чтения с кодировкой {enc}: {e}"
                    )
                )
                continue
        return None
