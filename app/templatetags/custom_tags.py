import re
from django import template

register = template.Library()


@register.filter
def check_int(value) -> int:
    try:
        return int(value)
    except TypeError:
        print('TypeError')
    except Exception as e:
        print(e)
    return -1


@register.filter
def concat_int(arg1, arg2):
    return int('%s%s' % (arg1, arg2))


@register.filter
def get_symbol(value):
    return str(value).strip('{}').strip(' ')


@register.filter
def replace_bad_html(value):
    matches = re.findall(r'<[^>]+>', value)
    return value.replace(matches[1], '')
