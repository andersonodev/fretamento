#!/usr/bin/env python3
"""
Script para corrigir o método _normalizar_nome_servico em todas as classes
"""

def melhorar_normalizacao():
    """Aplica a melhoria na normalização"""
    
    # Ler o arquivo
    with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Procurar e substituir as linhas do método
    for i, linha in enumerate(linhas):
        if 'def _normalizar_nome_servico(self, nome):' in linha:
            # Substituir as próximas linhas do método
            linhas[i+1] = '        """Normaliza nome do serviço para comparação"""\n'
            linhas[i+2] = '        import re\n'
            linhas[i+3] = '        \n'
            linhas[i+4] = '        nome_normalizado = nome.upper().strip()\n'
            linhas[i+5] = '        \n'
            linhas[i+6] = '        # Remover variações comuns que não afetam a compatibilidade\n'
            linhas[i+7] = '        nome_normalizado = re.sub(r\'\\s+\', \' \', nome_normalizado)  # Múltiplos espaços para um\n'
            linhas[i+8] = '        nome_normalizado = re.sub(r\'RJ\\s*\\(GIG\\)\', \'GIG\', nome_normalizado)  # RJ (GIG) -> GIG\n'
            linhas[i+9] = '        nome_normalizado = re.sub(r\'RJ\\s*\\(SDU\\)\', \'SDU\', nome_normalizado)  # RJ (SDU) -> SDU\n'
            linhas[i+10] = '        nome_normalizado = re.sub(r\'\\s*\\(GIG\\)\\s*\', \' GIG \', nome_normalizado)  # (GIG) -> GIG\n'
            linhas[i+11] = '        nome_normalizado = re.sub(r\'\\s*\\(SDU\\)\\s*\', \' SDU \', nome_normalizado)  # (SDU) -> SDU\n'
            linhas[i+12] = '        \n'
            linhas[i+13] = '        # Normalizar algumas variações específicas\n'
            linhas[i+14] = '        nome_normalizado = re.sub(r\'AEROPORTO\\s+INTER\\.\\s+GALEÃO\', \'AEROPORTO GALEÃO\', nome_normalizado)\n'
            linhas[i+15] = '        nome_normalizado = re.sub(r\'AEROPORTO\\s+SANTOS\\s+DUMONT\', \'AEROPORTO SDU\', nome_normalizado)\n'
            linhas[i+16] = '        \n'
            linhas[i+17] = '        # Remover pontuações desnecessárias\n'
            linhas[i+18] = '        nome_normalizado = re.sub(r\'[,\\.](?!\\d)\', \'\', nome_normalizado)  # Remove vírgulas e pontos (exceto em números)\n'
            linhas[i+19] = '        \n'
            linhas[i+20] = '        return nome_normalizado.strip()\n'
            
            # Pular as linhas antigas do método
            del linhas[i+21:i+22]  # Remove a linha "return nome.upper().strip()"
    
    # Escrever de volta
    with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    
    print("✅ Método _normalizar_nome_servico atualizado em todas as classes")

if __name__ == "__main__":
    melhorar_normalizacao()