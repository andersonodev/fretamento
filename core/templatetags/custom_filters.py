"""
Filtros personalizados para templates Django
"""

from django import template
from urllib.parse import urlencode

register = template.Library()


@register.filter
def querystring_without_page(get_dict):
    """Remove page parameter from querystring for pagination links"""
    mutable_dict = get_dict.copy()
    if 'page' in mutable_dict:
        del mutable_dict['page']
    
    query = urlencode(mutable_dict)
    return f'&{query}' if query else ''


@register.filter
def get_item(dictionary, key):
    """
    Filtro para acessar itens de dicionário no template
    Uso: {{ dict|get_item:key }}
    """
    if dictionary and hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None


@register.filter
def currency(value):
    """
    Formata valor como moeda brasileira
    Uso: {{ valor|currency }}
    """
    try:
        return f"R$ {float(value):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return "R$ 0,00"


@register.filter
def percentage(value):
    """
    Formata valor como percentual
    Uso: {{ valor|percentage }}
    """
    try:
        return f"{float(value):,.2f}%".replace('.', ',')
    except (ValueError, TypeError):
        return "0,00%"


@register.filter
def pax_badge(value):
    """
    Retorna classe CSS baseada no número de PAX
    Uso: {{ pax|pax_badge }}
    """
    try:
        pax = int(value)
        if pax <= 3:
            return "badge bg-primary"  # Executivo
        elif pax <= 11:
            return "badge bg-success"  # Van 15
        elif pax <= 14:
            return "badge bg-info"     # Van 18
        elif pax <= 26:
            return "badge bg-warning"  # Micro
        else:
            return "badge bg-danger"   # Ônibus
    except (ValueError, TypeError):
        return "badge bg-secondary"


@register.filter
def veiculo_icon(veiculo):
    """
    Retorna ícone FontAwesome baseado no tipo de veículo
    Uso: {{ veiculo|veiculo_icon }}
    """
    icons = {
        'Executivo': 'fas fa-car',
        'Van 15 lugares': 'fas fa-shuttle-van',
        'Van 18 lugares': 'fas fa-shuttle-van',
        'Micro': 'fas fa-bus',
        'Ônibus': 'fas fa-bus-alt'
    }
    return icons.get(veiculo, 'fas fa-question-circle')


@register.filter
def servico_color(tipo_servico):
    """
    Retorna classe de cor baseada no tipo de serviço
    Uso: {{ tipo|servico_color }}
    """
    colors = {
        'TRANSFER': 'text-primary',
        'DISPOSICAO': 'text-success',
        'TOUR': 'text-warning',
        'CITY_TOUR': 'text-info',
        'BY_NIGHT': 'text-primary'
    }
    return colors.get(tipo_servico, 'text-muted')


@register.simple_tag
def price_difference(price1, price2):
    """
    Calcula diferença entre dois preços
    Uso: {% price_difference preco1 preco2 %}
    """
    try:
        diff = float(price1) - float(price2)
        if diff > 0:
            return f"+R$ {diff:.2f}"
        elif diff < 0:
            return f"-R$ {abs(diff):.2f}"
        else:
            return "R$ 0,00"
    except (ValueError, TypeError):
        return "N/A"


@register.inclusion_tag('core/tags/price_card.html')
def price_card(title, price, subtitle="", icon="fas fa-dollar-sign", color="primary"):
    """
    Tag de inclusão para card de preço
    Uso: {% price_card "Título" preco "Subtítulo" "fas fa-icon" "success" %}
    """
    return {
        'title': title,
        'price': price,
        'subtitle': subtitle,
        'icon': icon,
        'color': color
    }


@register.filter
def multiply(value, arg):
    """
    Multiplica dois valores
    Uso: {{ valor|multiply:2 }}
    """
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def dict_keys(dictionary):
    """
    Retorna as chaves de um dicionário
    Uso: {{ dict|dict_keys }}
    """
    if dictionary and hasattr(dictionary, 'keys'):
        return list(dictionary.keys())
    return []


@register.filter
def dict_values(dictionary):
    """
    Retorna os valores de um dicionário
    Uso: {{ dict|dict_values }}
    """
    if dictionary and hasattr(dictionary, 'values'):
        return list(dictionary.values())
    return []


@register.filter
def date_br(value):
    """
    Formata data no formato brasileiro DD-MM-YYYY para uso em URLs
    Uso: {{ data|date_br }}
    """
    if value:
        try:
            if hasattr(value, 'strftime'):
                return value.strftime('%d-%m-%Y')
            else:
                from datetime import datetime
                date_obj = datetime.strptime(str(value), '%Y-%m-%d')
                return date_obj.strftime('%d-%m-%Y')
        except (ValueError, TypeError, AttributeError):
            pass
    return str(value) if value else ""