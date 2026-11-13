import sqlite3
from contextlib import closing
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from records.forms import MeasurementForm
from records.models import Measurement


class Command(BaseCommand):
    help = "Переносит записи из файла SQLite предыдущей версии в текущую базу."

    def add_arguments(self, parser):
        parser.add_argument("sqlite_file", type=Path)

    def handle(self, *args, **options):
        source = options["sqlite_file"].resolve()
        if not source.is_file():
            raise CommandError("Файл SQLite не найден.")

        added = skipped = 0
        try:
            with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as old_db:
                old_db.row_factory = sqlite3.Row
                rows = old_db.execute(
                    "SELECT patient, date, pulse, temperature FROM records_measurement"
                )
                with transaction.atomic():
                    for number, row in enumerate(rows, start=1):
                        form = MeasurementForm(dict(row))
                        if not form.is_valid():
                            raise CommandError(f"Строка {number}: неверные данные. Перенос отменён.")
                        _, created = Measurement.objects.get_or_create(**form.cleaned_data)
                        added += int(created)
                        skipped += int(not created)
        except sqlite3.DatabaseError as error:
            raise CommandError("Не удалось прочитать SQLite задания 4.") from error
        self.stdout.write(self.style.SUCCESS(f"Добавлено: {added}. Уже было: {skipped}."))
