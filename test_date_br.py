#!/usr/bin/env python
"""
Teste do filtro date_br
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from datetime import date
from django.template import Template, Context

def test_date_br_filter():
    """Testa se o filtro date_br está funcionando"""
    print("=== TESTANDO FILTRO date_br ===")
    
    try:
        template_content = """
        {% load custom_filters %}
        {{ data|date_br }}
        """
        
        template = Template(template_content)
        context = Context({'data': date(2025, 10, 4)})
        resultado = template.render(context).strip()
        
        print(f"✅ Filtro date_br funcionando: '{resultado}'")
        
        if resultado == "04-10-2025":
            print("✅ Formato correto: DD-MM-YYYY")
        else:
            print(f"❌ Formato incorreto. Esperado: '04-10-2025', Recebido: '{resultado}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no filtro date_br: {e}")
        return False

if __name__ == "__main__":
    test_date_br_filter()