# backend/logistics/models.py

from django.db import models
from django.db.models import Q, UniqueConstraint

PARTNER_CHOICES = [
    ("brenger",      "Brenger"),
    ("libero",       "Libero"),
    ("swdevries",    "Sw De Vries"),
    ("transpoksi",   "Transpoksi"),
    ("wuunder",      "Wuunder"),
    ("magic_movers", "Magic Movers"),
    ("tadde",        "Tadde"),
]


class InvoiceRun(models.Model):
    """
    Represents one execution of the delta pipeline for a single partner/invoice.
    """
    timestamp      = models.DateTimeField(auto_now_add=True)
    partner        = models.CharField(max_length=50, choices=PARTNER_CHOICES)
    invoice_number = models.CharField(
        max_length=100,
        db_index=True,
        blank=True,
        default="",
        help_text="Invoice number (empty for legacy or unparsed runs)"
    )
    delta_sum      = models.FloatField(help_text="Sum of all Delta values for this run")
    parsed_ok      = models.BooleanField(help_text="True if parsing succeeded")
    num_rows       = models.IntegerField(help_text="Number of invoice lines processed")

    class Meta:
        ordering = ["-timestamp"]
        constraints = [
            UniqueConstraint(
                fields=["partner", "invoice_number"],
                condition=~Q(invoice_number=""),
                name="unique_partner_invoice_number_nonempty"
            )
        ]
        verbose_name = "Invoice Run"
        verbose_name_plural = "Invoice Runs"

    def __str__(self):
        num = self.invoice_number or "(no #)"
        return f"{num} | {self.partner} | Δ={self.delta_sum}"


class InvoiceLine(models.Model):
    """
    One row of the delta comparison, linked to an InvoiceRun.
    Each partner has its own price_<partner> field.
    """
    run = models.ForeignKey(
        InvoiceRun,
        related_name="lines",
        on_delete=models.CASCADE,
        help_text="Parent InvoiceRun",
    )

    order_creation_date      = models.DateTimeField(help_text="Order creation timestamp")
    order_id                 = models.CharField("Order ID", max_length=100, db_index=True)
    weight                   = models.DecimalField(max_digits=10, decimal_places=2)
    route                    = models.CharField("buyer_country-seller_country", max_length=31)
    category_lvl_1_and_2     = models.CharField(max_length=100)
    category_lvl_2_and_3     = models.CharField(max_length=100)

    price_expected = models.DecimalField(
        "price",
        max_digits=12,
        decimal_places=2,
        help_text="Expected price from internal CMS",
    )

    price_brenger      = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_libero       = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_swdevries    = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_transpoksi   = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_wuunder      = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_magic_movers = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    price_tadde        = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    delta     = models.DecimalField(
        "Delta", max_digits=12, decimal_places=2, help_text="Actual minus expected"
    )
    delta_sum = models.DecimalField(
        "Delta_sum", max_digits=14, decimal_places=2, help_text="Total delta for parent run"
    )

    invoice_date   = models.DateField("Invoice date")
    invoice_number = models.CharField(max_length=100, db_index=True)

    class Meta:
        ordering = ["-run__timestamp", "order_creation_date"]
        indexes = [
            models.Index(fields=["order_id"]),
            models.Index(fields=["invoice_number"]),
        ]
        verbose_name = "Invoice Line"
        verbose_name_plural = "Invoice Lines"

    def __str__(self):
        return f"{self.order_creation_date:%Y-%m-%d} | {self.order_id} | Δ={self.delta:+.2f}"
