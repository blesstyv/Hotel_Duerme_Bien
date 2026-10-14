"""Small presentation helpers; no business rules live in the UI layer."""
from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

ICONS = {
    "bed": '<path d="M3 18v-9m18 9v-7a2 2 0 0 0-2-2H9v7M3 16h18M5 9h2v4H3M3 18v3m18-3v3"/>',
    "home": '<path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8"/>',
    "users": '<circle cx="9" cy="8" r="3"/><path d="M3 21v-3a6 6 0 0 1 12 0v3M16 5a3 3 0 0 1 0 6m2 4a5 5 0 0 1 3 5v1"/>',
    "user": '<circle cx="12" cy="7" r="4"/><path d="M4 21v-2a8 8 0 0 1 16 0v2"/>',
    "assignment": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8h6M9 12h6M9 16h4"/>',
    "chart": '<path d="M4 21V12m8 9V3m8 18V8"/>',
    "history": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "logout": '<path d="M10 4H4v16h6m3-13 5 5-5 5m-5-5h13"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "search": '<circle cx="10" cy="10" r="6"/><path d="m15 15 6 6"/>',
    "edit": '<path d="m15 4 5 5M4 20l5-1L21 7a2 2 0 0 0-4-4L5 15z"/>',
    "trash": '<path d="M3 6h18M9 6V3h6v3M5 6l1 15h12l1-15M10 10v7m4-7v7"/>',
    "check": '<path d="m5 12 4 4L19 6"/>',
    "close": '<path d="m6 6 12 12M6 18 18 6"/>',
    "arrow": '<path d="M4 12h16m-6-6 6 6-6 6"/>',
    "chevron": '<path d="m9 5 7 7-7 7"/>',
    "lock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2"/>',
    "unlock": '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0m-4 8v2"/>',
    "shield": '<path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6zM8 12l3 3 5-6"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.5"/>',
    "calendar": '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18M7 15h2m4 0h2"/>',
    "money": '<rect x="2" y="5" width="20" height="14" rx="2"/><circle cx="12" cy="12" r="3"/><path d="M5 9v.1m14 6v.1"/>',
    "filter": '<path d="M3 4h18l-7 8v7l-4 2v-9z"/>',
    "eye": '<path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>',
    "menu": '<path d="M4 6h16M4 12h16M4 18h16"/>',
    "moon": '<path d="M20 15A9 9 0 0 1 9 4a9 9 0 1 0 11 11Z"/>',
    "crown": '<path d="m3 6 4 4 5-6 5 6 4-4-2 12H5zM5 21h14"/>',
    "mail": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="m3 6 9 7 9-7"/>',
    "phone": '<path d="m8 3-4 1c-2 6 6 14 12 16l4-4-5-3-2 2c-3-1-5-3-6-6l2-2z"/>',
}


@register.simple_tag
def icon(name):
    return format_html('<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{}</svg>', mark_safe(ICONS.get(name, ICONS["info"])))


@register.filter
def clp(value):
    try:
        return "$" + format(int(value), ",").replace(",", ".")
    except (TypeError, ValueError):
        return "$0"


@register.filter
def initials(value):
    words = str(value or "").strip().split()
    return "".join(word[0] for word in words[:2]).upper() or "HB"


@register.filter
def dict_get(mapping, key):
    return (mapping or {}).get(str(key), [])


@register.filter
def as_string(value):
    return str(value)

