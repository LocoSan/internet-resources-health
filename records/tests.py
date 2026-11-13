import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase


class JsonRecordsTests(SimpleTestCase):
    record = {"patient": "Карточка А", "date": "2026-10-01", "pulse": 73, "temperature": "36.6"}

    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.enterContext(self.settings(RECORDS_DIR=self.directory))

    def test_empty_folder_has_message(self):
        self.assertContains(self.client.get("/"), "Записей пока нет")

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
