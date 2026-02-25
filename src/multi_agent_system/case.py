"""Case conversion."""

from __future__ import annotations

def to_snake(name):
    import re
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()

def to_camel(name):
    parts = name.split('_')
    return parts[0] + ''.join(x.title() for x in parts[1:])
