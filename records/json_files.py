import json
from uuid import uuid4

from django.conf import settings

from .forms import MAX_JSON_BYTES, MeasurementForm


MAX_JSON_ROWS = 500


def plain_record(values):
    return {
        "patient": values["patient"],
        "date": values["date"].isoformat(),
        "pulse": values["pulse"],
        "temperature": float(values["temperature"]),
    }


def validate_json(payload):
    rows = payload if isinstance(payload, list) else [payload]
    if not 1 <= len(rows) <= MAX_JSON_ROWS:
        raise ValueError(f"В файле должно быть от 1 до {MAX_JSON_ROWS} записей.")
    validated = []
    for number, row in enumerate(rows, start=1):
        if (
            not isinstance(row, dict)
            or set(row) != set(MeasurementForm.base_fields)
            or not isinstance(row["patient"], str)
            or not isinstance(row["date"], str)
            or type(row["pulse"]) is not int
            or type(row["temperature"]) not in (int, float)
        ):
            raise ValueError(f"Запись {number}: неверная структура.")
        form = MeasurementForm(row)
        if not form.is_valid():
            raise ValueError(f"Запись {number}: проверьте дату, пульс и температуру.")
        validated.append(plain_record(form.cleaned_data))
    return validated


def save_json(rows):
    directory = settings.RECORDS_DIR
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid4().hex}.json"
    temporary = path.with_suffix(".tmp")
    try:
        temporary.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def read_json_files():
    rows = []
    skipped = 0
    for path in sorted(settings.RECORDS_DIR.glob("*.json")):
        try:
            rows.extend(validate_json(json.loads(path.read_text(encoding="utf-8-sig"))))
        except (ValueError, OSError, RecursionError):
            skipped += 1
    return rows, skipped


def export_parts(rows):
    parts = []
    part = []
    size = 2
    for row in rows:
        encoded = json.dumps(row, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(part) == MAX_JSON_ROWS or size + len(encoded) + bool(part) > MAX_JSON_BYTES:
            parts.append(b"[" + b",".join(part) + b"]")
            part, size = [], 2
        size += len(encoded) + bool(part)
        part.append(encoded)
    if part:
        parts.append(b"[" + b",".join(part) + b"]")
    return parts
