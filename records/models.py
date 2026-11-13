from django.db import models


class Measurement(models.Model):
    patient = models.CharField(max_length=80)
    date = models.DateField()
    pulse = models.PositiveSmallIntegerField()
    temperature = models.DecimalField(max_digits=3, decimal_places=1)

    class Meta:
        ordering = ["-date", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["patient", "date", "pulse", "temperature"],
                name="unique_measurement",
            ),
        ]
