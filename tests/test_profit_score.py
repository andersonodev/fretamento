#!/usr/bin/env python3
"""
Teste rápido do filtro profit_score
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.templatetags.custom_filters import profit_score

def test_profit_score():
    """
    Testa o filtro profit_score
    """
    print("🔢 Testando filtro profit_score")
    print("=" * 40)
    
    test_values = [12.5, 0, None, 8.75, 15.0, 20.33]
    
    for value in test_values:
        result = profit_score(value)
        print(f"  {value} → {result}")
    
    print("\n✅ Teste profit_score concluído!")

if __name__ == "__main__":
    test_profit_score()