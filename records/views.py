import json

from django.db import IntegrityError, transaction
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from .forms import CreateForm, MeasurementForm, UploadForm
from .json_files import export_parts, plain_record, read_json_files, save_json, validate_json
from .models import Measurement


def show_page(request, form=None, upload_error="", status=200):
    source = "db" if request.GET.get("source") == "db" and not upload_error else "files"
    if source == "db":
        rows, skipped, parts = Measurement.objects.all(), 0, []
    else:
        rows, skipped = read_json_files()
        parts = range(1, len(export_parts(rows)) + 1)
    return render(request, "records/index.html", {
        "form": form if form is not None else CreateForm(initial={"storage": source}),
        "source": source,
        "upload_form": UploadForm(),
        "upload_error": upload_error,
        "rows": rows,
        "skipped": skipped,
        "parts": parts,
    }, status=status)


@require_http_methods(["GET", "POST"])
def index(request):
    if request.method == "POST":
        form = CreateForm(request.POST)
        if form.is_valid():
            values = form.cleaned_data.copy()
            if values.pop("storage") == "db":
                _, created = Measurement.objects.get_or_create(**values)
                if not created:
                    form.add_error(None, "Такая запись уже есть в базе.")
                    return show_page(request, form=form)
                return redirect(reverse("index") + "?source=db")
            save_json([plain_record(values)])
            return redirect("index")
        return show_page(request, form=form)
    return show_page(request)


@require_GET
def search(request):
    query = request.GET.get("q", "").strip()[:80].casefold()
    rows = [row for row in Measurement.objects.all() if query in row.patient.casefold()]
    return render(request, "records/db_table.html", {"rows": rows, "search": bool(query)})


@require_http_methods(["GET", "POST"])
def edit(request, pk):
    row = get_object_or_404(Measurement, pk=pk)
    form = MeasurementForm(
        request.POST if request.method == "POST" else None,
        initial=plain_record(vars(row)),
    )
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                Measurement.objects.filter(pk=pk).update(**form.cleaned_data)
        except IntegrityError:
            form.add_error(None, "Такая запись уже есть в базе.")
        else:
            return redirect(reverse("index") + "?source=db")
    return render(request, "records/edit.html", {"form": form})


@require_POST
def delete(request, pk):
    get_object_or_404(Measurement, pk=pk).delete()
    return redirect(reverse("index") + "?source=db")


@require_POST
def import_json(request):
    form = UploadForm(request.POST, request.FILES)
    if not form.is_valid():
        return show_page(request, upload_error=form.errors["file"][0], status=400)
    upload = form.cleaned_data["file"]
    try:
        rows = validate_json(json.loads(upload.read().decode("utf-8-sig")))
    except (UnicodeError, json.JSONDecodeError, RecursionError):
        return show_page(request, upload_error="Содержимое не является корректным JSON.", status=400)
    except ValueError as error:
        return show_page(request, upload_error=str(error), status=400)
    save_json(rows)
    return redirect("index")


@require_GET
def export_json(request):
    try:
        number = int(request.GET.get("part", "1"))
    except ValueError:
        raise Http404("Часть выгрузки не найдена.")
    rows, _ = read_json_files()
    parts = export_parts(rows)
    if not 1 <= number <= len(parts):
        raise Http404("Часть выгрузки не найдена.")
    response = HttpResponse(parts[number - 1], content_type="application/json")
    response["Content-Disposition"] = f'attachment; filename="measurements-{number}.json"'
    return response
