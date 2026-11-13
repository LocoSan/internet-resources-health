from django.urls import path

from records import views


urlpatterns = [
    path("", views.index, name="index"),
    path("import/", views.import_json, name="import_json"),
    path("export/", views.export_json, name="export_json"),
]
