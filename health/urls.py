from django.urls import path

from records import views


urlpatterns = [
    path("", views.index, name="index"),
    path("import/", views.import_json, name="import_json"),
    path("export/", views.export_json, name="export_json"),
    path("search/", views.search, name="search"),
    path("edit/<int:pk>/", views.edit, name="edit"),
    path("delete/<int:pk>/", views.delete, name="delete"),
]
