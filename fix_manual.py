#!/usr/bin/env python3

# Script para substituir métodos nas linhas específicas
with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'r') as f:
    linhas = f.readlines()

# Linha 514: return nome.upper().strip()
if len(linhas) > 514 and 'return nome.upper().strip()' in linhas[514]:
    linhas[514] = '''        import re
        
        nome_normalizado = nome.upper().strip()
        
        # Remover variações comuns que não afetam a compatibilidade
        nome_normalizado = re.sub(r'\\s+', ' ', nome_normalizado)  # Múltiplos espaços para um
        nome_normalizado = re.sub(r'RJ\\s*\\(GIG\\)', 'GIG', nome_normalizado)  # RJ (GIG) -> GIG
        nome_normalizado = re.sub(r'RJ\\s*\\(SDU\\)', 'SDU', nome_normalizado)  # RJ (SDU) -> SDU
        nome_normalizado = re.sub(r'\\s*\\(GIG\\)\\s*', ' GIG ', nome_normalizado)  # (GIG) -> GIG
        nome_normalizado = re.sub(r'\\s*\\(SDU\\)\\s*', ' SDU ', nome_normalizado)  # (SDU) -> SDU
        
        # Normalizar algumas variações específicas
        nome_normalizado = re.sub(r'AEROPORTO\\s+INTER\\.\\s+GALEÃO', 'AEROPORTO GALEÃO', nome_normalizado)
        nome_normalizado = re.sub(r'AEROPORTO\\s+SANTOS\\s+DUMONT', 'AEROPORTO SDU', nome_normalizado)
        
        # Remover pontuações desnecessárias
        nome_normalizado = re.sub(r'[,\\.](?!\\d)', '', nome_normalizado)  # Remove vírgulas e pontos (exceto em números)
        
        return nome_normalizado.strip()
'''

# Linha 793: return nome.upper().strip()
if len(linhas) > 793 and 'return nome.upper().strip()' in linhas[793]:
    linhas[793] = '''        import re
        
        nome_normalizado = nome.upper().strip()
        
        # Remover variações comuns que não afetam a compatibilidade
        nome_normalizado = re.sub(r'\\s+', ' ', nome_normalizado)  # Múltiplos espaços para um
        nome_normalizado = re.sub(r'RJ\\s*\\(GIG\\)', 'GIG', nome_normalizado)  # RJ (GIG) -> GIG
        nome_normalizado = re.sub(r'RJ\\s*\\(SDU\\)', 'SDU', nome_normalizado)  # RJ (SDU) -> SDU
        nome_normalizado = re.sub(r'\\s*\\(GIG\\)\\s*', ' GIG ', nome_normalizado)  # (GIG) -> GIG
        nome_normalizado = re.sub(r'\\s*\\(SDU\\)\\s*', ' SDU ', nome_normalizado)  # (SDU) -> SDU
        
        # Normalizar algumas variações específicas
        nome_normalizado = re.sub(r'AEROPORTO\\s+INTER\\.\\s+GALEÃO', 'AEROPORTO GALEÃO', nome_normalizado)
        nome_normalizado = re.sub(r'AEROPORTO\\s+SANTOS\\s+DUMONT', 'AEROPORTO SDU', nome_normalizado)
        
        # Remover pontuações desnecessárias
        nome_normalizado = re.sub(r'[,\\.](?!\\d)', '', nome_normalizado)  # Remove vírgulas e pontos (exceto em números)
        
        return nome_normalizado.strip()
'''

# Escrever de volta
with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'w') as f:
    f.writelines(linhas)

print("✅ Métodos _normalizar_nome_servico atualizados")