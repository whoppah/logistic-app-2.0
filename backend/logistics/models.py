#backend/logistics/models.py
from django.db import models


class InvoiceRun(models.Model):
    PARTNER_CHOICES = [
        ("brenger", "Brenger"),
        ("wuunder", "Wuunder"),
        ("libero", "Libero"),
        ("swdevries", "Sw De Vries"),
        # add others if needed
    ]

    timestamp    = models.DateTimeField(auto_now_add=True)
    partner      = models.CharField(max_length=50, choices=PARTNER_CHOICES)
    delta_sum    = models.FloatField()
    parsed_ok    = models.BooleanField()
    num_rows     = models.IntegerField()

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {self.partner} | Δ={self.delta_sum}"
