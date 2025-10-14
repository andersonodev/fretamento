#!/usr/bin/env python3
"""
Script para limpar dados importados anteriormente e reimportar corretamente
a planilha de controle de Van - Outubro 2025.
"""

import os
import sys
import django

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico
from escalas.models import Escala, AlocacaoVan
from django.contrib.auth.models import User


def limpar_dados_outubro():
    """Remove todos os dados importados de outubro 2025"""
    print("Limpando dados importados anteriormente...")
    
    # Buscar escalas de outubro 2025
    escalas_outubro = Escala.objects.filter(
        data__year=2025,
        data__month=10
    )
    
    print(f"Encontradas {escalas_outubro.count()} escalas de outubro 2025")
    
    # Remover alocações
    alocacoes_removidas = 0
    for escala in escalas_outubro:
        count = escala.alocacoes.count()
        escala.alocacoes.all().delete()
        alocacoes_removidas += count
    
    print(f"Removidas {alocacoes_removidas} alocações")
    
    # Remover serviços do arquivo
    servicos_arquivo = Servico.objects.filter(
        arquivo_origem='VAN FRETAMENTO CONTROLE - Outubro 25.csv'
    )
    servicos_count = servicos_arquivo.count()
    servicos_arquivo.delete()
    
    print(f"Removidos {servicos_count} serviços")
    
    # Remover escalas vazias
    escalas_count = escalas_outubro.count()
    escalas_outubro.delete()
    
    print(f"Removidas {escalas_count} escalas")
    print("Limpeza concluída!")


def main():
    """Função principal"""
    print("Limpeza e Reimportação de Dados - Outubro 2025")
    print("=" * 60)
    
    resposta = input("Deseja LIMPAR todos os dados de outubro e reimportar? (s/N): ")
    if resposta.lower() != 's':
        print("Operação cancelada.")
        return
    
    # Limpar dados existentes
    limpar_dados_outubro()
    
    print("\n" + "=" * 60)
    print("Agora execute o script de importação novamente:")
    print("python scripts/importar_dados_planilha_outubro.py")


if __name__ == '__main__':
    main()