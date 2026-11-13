from django import forms


class MeasurementForm(forms.Form):
    patient = forms.CharField(label="Имя учебной карточки", max_length=80)
    date = forms.DateField(label="Дата", input_formats=["%Y-%m-%d"], widget=forms.DateInput(
        format="%Y-%m-%d", attrs={"type": "date"}
    ))
    pulse = forms.IntegerField(label="Пульс, уд/мин", min_value=1, max_value=300)
    temperature = forms.DecimalField(
        label="Температура, °C", min_value=20, max_value=50, max_digits=3, decimal_places=1,
        localize=False,
    )


class UploadForm(forms.Form):
    file = forms.FileField(label="Файл JSON", widget=forms.ClearableFileInput(attrs={"accept": ".json"}))
