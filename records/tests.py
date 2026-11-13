import json
import sqlite3
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from .models import Measurement


class JsonRecordsTests(SimpleTestCase):
    record = {"patient": "Карточка А", "date": "2026-10-01", "pulse": 73, "temperature": "36.6"}

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.enterContext(self.settings(RECORDS_DIR=self.directory))

    def test_empty_folder_has_message(self):
        response = self.client.get("/")
        self.assertContains(response, "Записей пока нет")
        self.assertNotContains(response, "/export/")
        self.assertEqual(self.client.get("/export/").status_code, 404)

    def test_form_writes_valid_record(self):
        self.assertRedirects(self.client.post("/", self.record), "/")
        self.assertEqual(len(list(self.directory.glob("*.json"))), 1)
        self.assertContains(self.client.get("/"), "Карточка А")

    def test_invalid_input_is_not_saved(self):
        self.assertContains(self.client.post("/", {**self.record, "pulse": -1}), "ошибки")
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_upload_reads_all_files_and_ignores_original_name(self):
        for name, patient in [("first.json", "Карточка А"), ("second.json", "Карточка Б")]:
            content = json.dumps({**self.record, "patient": patient, "temperature": 36.6}).encode()
            upload = SimpleUploadedFile(name, content)
            self.assertRedirects(self.client.post("/import/", {"file": upload}), "/")
        response = self.client.get("/")
        self.assertContains(response, "Карточка А")
        self.assertContains(response, "Карточка Б")
        self.assertNotIn("first.json", [file.name for file in self.directory.iterdir()])
        response = self.client.get("/export/")
        self.assertEqual(len(response.json()), 2)
        self.assertIn("attachment", response.headers["Content-Disposition"])

    def test_broken_upload_is_removed(self):
        for content in (b"{", b'{"pulse": 80}', b"[]"):
            upload = SimpleUploadedFile("broken.json", content)
            response = self.client.post("/import/", {"file": upload})
            self.assertContains(response, "Файл отклонён", status_code=400)
            self.assertEqual(list(self.directory.iterdir()), [])

    def test_large_export_can_be_imported_part_by_part(self):
        record = {**self.record, "temperature": 36.6}
        for name in ("a.json", "b.json"):
            (self.directory / name).write_text(
                json.dumps([record] * 300, ensure_ascii=False), encoding="utf-8"
            )

        first = self.client.get("/export/")
        second = self.client.get("/export/?part=2")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json() + second.json(), [record] * 600)
        self.assertContains(self.client.get("/"), "/export/?part=2")
        self.assertEqual(self.client.get("/export/?part=3").status_code, 404)
        for part in (first, second):
            upload = SimpleUploadedFile("part.json", part.content)
            self.assertRedirects(self.client.post("/import/", {"file": upload}), "/")

    def test_export_respects_byte_limit_when_rows_need_escaping(self):
        record = {**self.record, "patient": "A" + "\x1f" * 78 + "B", "temperature": 36.6}
        for name in ("a.json", "b.json"):
            (self.directory / name).write_text(json.dumps([record] * 250), encoding="utf-8")

        first = self.client.get("/export/")
        second = self.client.get("/export/?part=2")
        self.assertEqual(first.json() + second.json(), [record] * 500)
        for part in (first, second):
            self.assertLessEqual(len(part.content), 256 * 1024)


class DatabaseRecordsTests(TestCase):
    record = JsonRecordsTests.record

    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.settings_dir = temporary.name
        self.enterContext(self.settings(RECORDS_DIR=Path(temporary.name)))

    def test_database_create_duplicate_and_read(self):
        data = {**self.record, "storage": "db"}
        self.assertRedirects(self.client.post("/", data), "/?source=db")
        response = self.client.post("/", data)
        self.assertContains(response, "Такая запись уже есть")
        self.assertEqual(self.client.get("/?source=db").context["rows"].count(), 1)
        self.assertNotContains(self.client.get("/?source=files"), "Карточка А")

    def test_search_edit_and_delete(self):
        self.client.post("/", {**self.record, "storage": "db", "patient": "КАРТОЧКА А"})
        self.client.post("/", {**self.record, "storage": "db", "patient": "Другая карточка"})
        response = self.client.get("/search/", {"q": "карточка а"})
        self.assertContains(response, "КАРТОЧКА А")
        self.assertNotContains(response, "Другая карточка")

        row = self.client.get("/?source=db").context["rows"].get(patient="КАРТОЧКА А")
        self.assertContains(self.client.post(f"/edit/{row.pk}/", {**self.record, "pulse": 999}), "ошибки")
        row.refresh_from_db()
        self.assertEqual(row.pulse, 73)
        self.assertRedirects(
            self.client.post(f"/edit/{row.pk}/", {**self.record, "pulse": 84}), "/?source=db"
        )
        row.refresh_from_db()
        self.assertEqual(row.pulse, 84)
        self.assertEqual(self.client.get(f"/delete/{row.pk}/").status_code, 405)
        self.assertRedirects(self.client.post(f"/delete/{row.pk}/"), "/?source=db")
        self.assertContains(self.client.get("/?source=db"), "Другая карточка")
        self.assertNotContains(self.client.get("/?source=db"), "Карточка А")

    def test_import_sqlite_transfers_existing_rows_without_duplicates(self):
        source = Path(self.settings_dir) / "old.sqlite3"
        connection = sqlite3.connect(source)
        try:
            with connection:
                connection.execute("CREATE TABLE records_measurement (patient, date, pulse, temperature)")
                connection.execute("INSERT INTO records_measurement VALUES (?, ?, ?, ?)", (
                    "Старая карточка", "2026-10-01", 73, 36.6,
                ))
        finally:
            connection.close()

        for _ in range(2):
            call_command("import_sqlite", source, stdout=StringIO())
        self.assertEqual(Measurement.objects.count(), 1)
        row = Measurement.objects.get()
        self.assertEqual((row.patient, row.date.isoformat(), row.pulse, str(row.temperature)),
                         ("Старая карточка", "2026-10-01", 73, "36.6"))
