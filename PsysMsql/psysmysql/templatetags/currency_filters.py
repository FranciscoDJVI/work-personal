from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_currency_cop(value):
    try:
        numeric_value = float(value)
        formatted_string = "{:,.2f}".format(numeric_value)

        formatted_string = (
            formatted_string.replace(",", "TEMP").replace(".", ",").replace("TEMP", ".")
        )
        return mark_safe(f"$ {formatted_string}")
    except (ValueError, TypeError):
        return ""


@register.filter()
def mult(value, value2):
    try:
        return int(value) * float(value2)
    except (ValueError, TypeError):
        return ""
