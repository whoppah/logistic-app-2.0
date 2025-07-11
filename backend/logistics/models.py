#backend/logistics/models.py
from django.db import models

PARTNER_CHOICES = [
    ("brenger", "Brenger"),
    ("libero", "Libero"),
    ("swdevries", "Sw De Vries"),
    ("transpoksi", "Transpoksi"),
    ("wuunder", "Wuunder"),
    ("magic_movers", "Magic Movers"),
    ("tadde", "Tadde"),
]


class InvoiceRun(models.Model):
    """
    Represents a single execution of the invoice delta pipeline for one partner.
    """
    timestamp    = models.DateTimeField(auto_now_add=True)
    partner      = models.CharField(max_length=50, choices=PARTNER_CHOICES)
    delta_sum    = models.FloatField(
        help_text="Sum of all Delta values for this run"
    )
    parsed_ok    = models.BooleanField(
        help_text="True if any invoice rows were successfully parsed"
    )
    num_rows     = models.IntegerField(
        help_text="Number of invoice lines processed"
    )

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.timestamp:%Y-%m-%d %H:%M} | {self.partner} | Δ={self.delta_sum}"


class InvoiceLine(models.Model):
    """
    One row of the delta comparison output, linked to an InvoiceRun.
    """
    run = models.ForeignKey(
        InvoiceRun,
        related_name="lines",
        on_delete=models.CASCADE,
        help_text="The parent InvoiceRun for this row"
    )

    order_creation_date      = models.DateTimeField(
        help_text="When the order was created in the system"
    )
    order_id                 = models.CharField(
        "Order ID",
        max_length=100,
        db_index=True,
        help_text="UUID or identifier of the order"
    )
    weight                   = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Weight (kg) as parsed from the invoice"
    )
    route                    = models.CharField(
        "buyer_country-seller_country",
        max_length=31,
        help_text="Concatenated route key, e.g. NL-DE"
    )
    category_lvl_1_and_2     = models.CharField(
        max_length=100,
        help_text="Category level 1 and 2"
    )
    category_lvl_2_and_3     = models.CharField(
        max_length=100,
        help_text="Category level 2 and 3"
    )

    price_expected           = models.DecimalField(
        "price",
        max_digits=12,
        decimal_places=2,
        help_text="Expected price from internal CMS"
    )
    price_actual             = models.DecimalField(
        "price_{partner}",
        max_digits=12,
        decimal_places=2,
        help_text="Actual price charged by the partner"
    )

    delta                    = models.DecimalField(
        "Delta",
        max_digits=12,
        decimal_places=2,
        help_text="Difference = actual - expected"
    )
    delta_sum                = models.DecimalField(
        "Delta_sum",
        max_digits=14,
        decimal_places=2,
        help_text="Total delta for the parent run"
    )

    invoice_date             = models.DateField(
        "Invoice date",
        help_text="Date on the invoice"
    )
    invoice_number           = models.CharField(
        max_length=100,
        db_index=True,
        help_text="Invoice identifier"
    )

    class Meta:
        ordering = ["-run__timestamp", "order_creation_date"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["invoice_number"]),
        ]

    def __str__(self):
        return (
            f"{self.order_creation_date:%Y-%m-%d} | {self.order_id} | "
            f"Δ={self.delta:+.2f}"
        )
