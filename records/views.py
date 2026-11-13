import json

from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import MeasurementForm, UploadForm
from .json_files import plain_record, read_json_files, save_json, validate_json


def show_page(request, form=None, upload_error="", status=200):
    rows, skipped = read_json_files()
    return render(request, "records/index.html", {
        "form": form if form is not None else MeasurementForm(),
        "upload_form": UploadForm(),
        "upload_error": upload_error,
        "rows": rows,
        "skipped": skipped,
    }, status=status)


@require_http_methods(["GET", "POST"])
def index(request):
    if request.method == "POST":
        form = MeasurementForm(request.POST)
        if form.is_valid():
            save_json([plain_record(form.cleaned_data)])
            return redirect("index")
        return show_page(request, form=form)
    return show_page(request)


@require_POST
def import_json(request):
    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return show_page(request, upload_error="Выберите непустой файл JSON.", status=400)
    upload = form.cleaned_data["file"]
    try:
        if upload.size > 256 * 1024:
            raise ValueError("Размер файла больше 256 КБ.")
        rows = validate_json(json.loads(upload.read().decode("utf-8-sig")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        return show_page(request, upload_error="Содержимое не является корректным JSON.", status=400)
    except ValueError as error:
        return show_page(request, upload_error=str(error), status=400)
    save_json(rows)
    return redirect("index")


@require_GET
def export_json(request):
    rows, _ = read_json_files()
    response = JsonResponse(rows, safe=False, json_dumps_params={"ensure_ascii": False, "indent": 2})
    response["Content-Disposition"] = 'attachment; filename="measurements.json"'
    return response
