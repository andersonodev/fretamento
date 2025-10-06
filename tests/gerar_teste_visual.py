#!/usr/bin/env python3
"""
Gera arquivo Excel de teste para verificação visual das cores
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from escalas.models import Escala
from escalas.services import ExportadorEscalas
from datetime import datetime

def gerar_excel_teste():
    """Gera arquivo Excel para verificação visual"""
    
    print("📊 Gerando arquivo Excel de teste...")
    
    try:
        # Buscar uma escala
        escala = Escala.objects.first()
        if not escala:
            print("❌ Nenhuma escala encontrada")
            return False
        
        # Exportar para Excel
        exportador = ExportadorEscalas()
        excel_data = exportador.exportar_para_excel(escala)
        
        # Salvar arquivo
        filename = f"teste_formatacao_condicional_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        with open(filename, 'wb') as f:
            f.write(excel_data)
        
        print(f"✅ Arquivo gerado: {filename}")
        print("🎨 Abra o arquivo no Excel para verificar:")
        print("   • Valores negativos na coluna 'Rent Van 01' devem estar VERMELHOS")
        print("   • Valores positivos na coluna 'Rent Van 01' devem estar VERDES")
        
        # Também gerar arquivo mensal
        escalas = Escala.objects.all()[:2]
        if escalas:
            excel_mensal = exportador.exportar_mes_para_excel(escalas)
            filename_mensal = f"teste_formatacao_mensal_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            with open(filename_mensal, 'wb') as f:
                f.write(excel_mensal)
            print(f"✅ Arquivo mensal gerado: {filename_mensal}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro: {str(e)}")
        return False

if __name__ == "__main__":
    sucesso = gerar_excel_teste()
    if sucesso:
        print("\n🎉 Arquivos de teste gerados com sucesso!")
        print("📂 Abra os arquivos .xlsx para verificar as cores")
    else:
        print("\n💥 Falha na geração dos arquivos!")