#!/usr/bin/env python3
"""
Teste das Correções de Interface - Calendários e Supervisor
Script para verificar se as correções foram aplicadas corretamente
"""

import os
import re
from pathlib import Path

def testar_calendarios_portugues():
    """Testa se todos os campos de data têm lang='pt-BR'"""
    print("🔍 TESTANDO CALENDÁRIOS EM PORTUGUÊS...")
    
    templates_dir = Path('templates')
    campos_data_sem_lang = []
    campos_data_com_lang = []
    
    # Buscar todos os arquivos HTML
    for html_file in templates_dir.rglob('*.html'):
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Encontrar todos os campos type="date"
        date_fields = re.findall(r'<input[^>]*type="date"[^>]*>', content)
        
        for field in date_fields:
            if 'lang="pt-BR"' in field:
                campos_data_com_lang.append(f"{html_file}: {field[:80]}...")
            else:
                campos_data_sem_lang.append(f"{html_file}: {field[:80]}...")
    
    print(f"✅ Campos de data COM lang='pt-BR': {len(campos_data_com_lang)}")
    for campo in campos_data_com_lang[:5]:  # Mostrar apenas 5 primeiros
        print(f"   📅 {campo}")
    
    if campos_data_sem_lang:
        print(f"❌ Campos de data SEM lang='pt-BR': {len(campos_data_sem_lang)}")
        for campo in campos_data_sem_lang:
            print(f"   ⚠️ {campo}")
        return False
    else:
        print("✅ Todos os campos de data têm localização em português!")
        return True

def testar_remocao_supervisor():
    """Testa se a palavra 'Supervisor' foi removida/substituída"""
    print("\n🔍 TESTANDO REMOÇÃO/SUBSTITUIÇÃO DE 'SUPERVISOR'...")
    
    templates_dir = Path('templates')
    ocorrencias_supervisor = []
    
    # Buscar arquivos HTML principais (não _old ou _backup)
    for html_file in templates_dir.rglob('*.html'):
        if '_old' in str(html_file) or '_backup' in str(html_file):
            continue
            
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Buscar ocorrências de 'supervisor' (case insensitive)
        if re.search(r'supervisor', content, re.IGNORECASE):
            lines = content.split('\n')
            for i, line in enumerate(lines, 1):
                if re.search(r'supervisor', line, re.IGNORECASE):
                    ocorrencias_supervisor.append(f"{html_file}:{i} - {line.strip()}")
    
    if ocorrencias_supervisor:
        print(f"⚠️ Ainda existem {len(ocorrencias_supervisor)} ocorrências de 'Supervisor':")
        for ocorrencia in ocorrencias_supervisor:
            print(f"   📍 {ocorrencia}")
        return False
    else:
        print("✅ Palavra 'Supervisor' removida/substituída com sucesso!")
        return True

def verificar_substituicoes_corretas():
    """Verifica se as substituições foram feitas corretamente"""
    print("\n🔍 VERIFICANDO SUBSTITUIÇÕES CORRETAS...")
    
    # Verificar se 'Administrador' foi adicionado
    base_html = Path('templates/base.html')
    home_html = Path('templates/core/home.html')
    
    sucesso = True
    
    if base_html.exists():
        with open(base_html, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'Administrador' in content:
            print("✅ base.html: 'Administrador' encontrado")
        else:
            print("❌ base.html: 'Administrador' NÃO encontrado")
            sucesso = False
    
    if home_html.exists():
        with open(home_html, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'Administrador' in content:
            print("✅ home.html: 'Administrador' encontrado")
        else:
            print("❌ home.html: 'Administrador' NÃO encontrado")
            sucesso = False
    
    return sucesso

def main():
    """Executa todos os testes"""
    print("=" * 60)
    print("🧪 TESTE DAS CORREÇÕES DE INTERFACE")
    print("=" * 60)
    
    resultados = []
    
    # Teste 1: Calendários em português
    resultados.append(testar_calendarios_portugues())
    
    # Teste 2: Remoção de supervisor
    resultados.append(testar_remocao_supervisor())
    
    # Teste 3: Verificar substituições
    resultados.append(verificar_substituicoes_corretas())
    
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    if all(resultados):
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Calendários em português: OK")
        print("✅ Remoção de supervisor: OK")
        print("✅ Substituições corretas: OK")
        return True
    else:
        print("❌ ALGUNS TESTES FALHARAM!")
        print(f"❌ Calendários em português: {'OK' if resultados[0] else 'FALHOU'}")
        print(f"❌ Remoção de supervisor: {'OK' if resultados[1] else 'FALHOU'}")
        print(f"❌ Substituições corretas: {'OK' if resultados[2] else 'FALHOU'}")
        return False

if __name__ == "__main__":
    import os
    os.chdir('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
    success = main()
    exit(0 if success else 1)