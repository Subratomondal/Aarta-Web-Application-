from django import template

register = template.Library()

STATUS_ORDER = {
    'pending': 0,
    'confirmed': 1,
    'shipped': 2,
    'delivered': 3,
}

@register.filter
def step_reached(current_status, step_name):
    return STATUS_ORDER.get(current_status, 0) >= STATUS_ORDER.get(step_name, 0)

@register.filter(name='add_class')
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter
def mul(value, arg):
    return value * arg

@register.filter
def order_badge_class(status):
    return {
        'pending': 'bg-gray-100 text-gray-700',
        'confirmed': 'bg-yellow-100 text-yellow-700',
        'shipped': 'bg-blue-100 text-blue-700',
        'delivered': 'bg-green-100 text-green-700',
        'canceled': 'bg-red-100 text-red-700',
    }.get(status, 'bg-gray-100 text-gray-700')

@register.filter
def progress_width(status):
    width_map = {
        'pending': '0%',
        'confirmed': '33%',
        'shipped': '66%',
        'delivered': '100%',
    }
    return width_map.get(status, '0%')

@register.simple_tag
def order_steps():
    return ['pending', 'confirmed', 'shipped', 'delivered']

@register.filter
def index(sequence, position):
    try:
        return sequence[position]
    except IndexError:
        return ''

@register.filter
def split(value, delimiter=","):
    return value.split(delimiter)