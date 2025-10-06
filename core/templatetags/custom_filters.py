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
    Formata valor como moeda brasileira (R$ 1.234,56)
    Uso: {{ valor|currency }}
    """
    try:
        if value is None:
            return "R$ 0,00"
        
        # Converter para float
        num = float(value)
        
        # Formatar com separadores brasileiros
        if num == 0:
            return "R$ 0,00"
        elif abs(num) < 0.01:
            return "R$ 0,00"
        else:
            # Usar formatação brasileira: R$ 1.234,56
            formatted = f"R$ {num:,.2f}"
            # Trocar ponto por vírgula e vírgula por ponto
            formatted = formatted.replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
            return formatted
    except (ValueError, TypeError, AttributeError):
        return "R$ 0,00"


@register.filter
def currency_compact(value):
    """
    Formata valor como moeda brasileira compacta (para espaços pequenos)
    Uso: {{ valor|currency_compact }}
    """
    try:
        if value is None:
            return "R$ 0"
        
        num = float(value)
        
        if num == 0:
            return "R$ 0"
        elif abs(num) >= 1000000:
            return f"R$ {num/1000000:.1f}M".replace('.', ',')
        elif abs(num) >= 1000:
            return f"R$ {num/1000:.1f}K".replace('.', ',')
        elif abs(num) >= 100:
            return f"R$ {num:.0f}"
        else:
            return f"R$ {num:.2f}".replace('.', ',')
    except (ValueError, TypeError, AttributeError):
        return "R$ 0"


@register.filter
def currency_no_cents(value):
    """
    Formata valor como moeda brasileira sem centavos (R$ 1.234)
    Uso: {{ valor|currency_no_cents }}
    """
    try:
        if value is None:
            return "R$ 0"
        
        num = float(value)
        if num == 0:
            return "R$ 0"
        else:
            formatted = f"R$ {num:,.0f}"
            # Aplicar formatação brasileira
            formatted = formatted.replace(',', '.')
            return formatted
    except (ValueError, TypeError, AttributeError):
        return "R$ 0"


@register.filter
def percentage(value):
    """
    Formata valor como percentual brasileiro
    Uso: {{ valor|percentage }}
    """
    try:
        if value is None:
            return "0,00%"
        
        num = float(value)
        return f"{num:.2f}%".replace('.', ',')
    except (ValueError, TypeError, AttributeError):
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


@register.filter
def number_br(value):
    """
    Formata números com separadores brasileiros (1.234,56)
    Uso: {{ numero|number_br }}
    """
    try:
        if value is None:
            return "0"
        
        num = float(value)
        if num == int(num):
            # Número inteiro
            return f"{int(num):,}".replace(',', '.')
        else:
            # Número decimal
            return f"{num:,.2f}".replace(',', 'TEMP').replace('.', ',').replace('TEMP', '.')
    except (ValueError, TypeError, AttributeError):
        return "0"


@register.simple_tag
def price_difference(price1, price2):
    """
    Calcula diferença entre dois preços em formato brasileiro
    Uso: {% price_difference preco1 preco2 %}
    """
    try:
        if price1 is None or price2 is None:
            return "N/A"
        
        diff = float(price1) - float(price2)
        if diff > 0:
            formatted = f"+R$ {diff:.2f}".replace('.', ',')
            return formatted
        elif diff < 0:
            formatted = f"-R$ {abs(diff):.2f}".replace('.', ',')
            return formatted
        else:
            return "R$ 0,00"
    except (ValueError, TypeError, AttributeError):
        return "N/A"


@register.simple_tag
def price_percentage_change(old_price, new_price):
    """
    Calcula variação percentual entre dois preços
    Uso: {% price_percentage_change preco_antigo preco_novo %}
    """
    try:
        if old_price is None or new_price is None or float(old_price) == 0:
            return "N/A"
        
        old_val = float(old_price)
        new_val = float(new_price)
        
        change = ((new_val - old_val) / old_val) * 100
        
        if change > 0:
            return f"+{change:.1f}%".replace('.', ',')
        elif change < 0:
            return f"{change:.1f}%".replace('.', ',')
        else:
            return "0,0%"
    except (ValueError, TypeError, AttributeError, ZeroDivisionError):
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
def price_per_pax(price, pax):
    """
    Calcula preço por PAX em formato brasileiro
    Uso: {{ preco|price_per_pax:pax }}
    """
    try:
        if price is None or pax is None or int(pax) == 0:
            return "R$ 0,00"
        
        per_pax = float(price) / int(pax)
        return f"R$ {per_pax:.2f}".replace('.', ',')
    except (ValueError, TypeError, AttributeError, ZeroDivisionError):
        return "R$ 0,00"


@register.filter
def profit_margin(revenue, cost):
    """
    Calcula margem de lucro em percentual
    Uso: {{ receita|profit_margin:custo }}
    """
    try:
        if revenue is None or cost is None or float(revenue) == 0:
            return "0,00%"
        
        margin = ((float(revenue) - float(cost)) / float(revenue)) * 100
        return f"{margin:.2f}%".replace('.', ',')
    except (ValueError, TypeError, AttributeError, ZeroDivisionError):
        return "0,00%"


@register.filter
def price_color_class(value, threshold=500):
    """
    Retorna classe CSS baseada no valor do preço
    Uso: {{ preco|price_color_class:1000 }}
    """
    try:
        price = float(value) if value else 0
        thresh = float(threshold)
        
        if price >= thresh * 2:
            return "text-success fw-bold"  # Verde para preços altos
        elif price >= thresh:
            return "text-primary fw-bold"  # Azul para preços médios
        elif price >= thresh * 0.5:
            return "text-warning"         # Amarelo para preços baixos
        else:
            return "text-danger"          # Vermelho para preços muito baixos
    except (ValueError, TypeError, AttributeError):
        return "text-muted"


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


@register.filter
def profit_score(value):
    """
    Formata score de lucratividade (valor por PAX)
    Uso: {{ lucratividade|profit_score }}
    """
    try:
        if value is None or value == 0:
            return "0,00"
        
        value = float(value)
        return f"{value:.2f}".replace('.', ',')
    except (ValueError, TypeError):
        return "0,00"