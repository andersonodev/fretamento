#!/usr/bin/env python
"""
Script para corrigir o erro van=None na linha 427
"""

def fix_van_none_error_427():
    file_path = '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py'
    
    # Ler o arquivo
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Encontrar e corrigir a linha 427 (índice 426)
    if len(lines) > 426:
        original_line = lines[426]
        if 'van=None' in original_line:
            # Remover van=None da linha
            fixed_line = original_line.replace(', van=None', '')
            lines[426] = fixed_line
            print(f"Linha 427 original: {original_line.strip()}")
            print(f"Linha 427 corrigida: {fixed_line.strip()}")
        else:
            print("Linha 427 não contém 'van=None'")
    else:
        print("Arquivo não tem linha 427")
    
    # Escrever o arquivo corrigido
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print("Arquivo corrigido com sucesso!")

if __name__ == '__main__':
    fix_van_none_error_427()