from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name="as_bound")
def as_bound(form, field_name):
    """
    Return form[field_name] (a BoundField) or empty string if missing.
    Used as: {{ form|as_bound:"inventory_id" }}
    """
    try:
        return form[field_name]
    except Exception:
        return ""

@register.filter(name="safe_crispy")
def safe_crispy(field):
    """
    Try to render a BoundField via crispy (if installed). If not,
    fall back to str(field) so the template still compiles.
    """
    try:
        # Lazy import to avoid hard dependency if crispy isn't present in tests
        from crispy_forms.templatetags.crispy_forms_filters import as_crispy_field
        return mark_safe(as_crispy_field(field))
    except Exception:
        return mark_safe(str(field))