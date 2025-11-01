from django import template
from django.forms.boundfield import BoundField

register = template.Library()

@register.filter
def as_bound(form, name):
    """
    Resolve a field *name* (string) to a BoundField from the given form.
    Usage:
        {{ form|as_bound:"inventory_id"|as_crispy_field }}
    Or inside a loop over names:
        {% for name in field_names %}
          {{ form|as_bound:name|as_crispy_field }}
        {% endfor %}
    """
    if not form or not name:
        return ""
    try:
        bf = form[name]
        return bf if isinstance(bf, BoundField) else ""
    except Exception:
        return ""