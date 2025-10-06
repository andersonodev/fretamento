#!/usr/bin/env python3
"""
Aplicar a normalização melhorada no arquivo views.py
"""

# Novo método melhorado
novo_metodo = '''    def _normalizar_nome_servico(self, nome):
        """Normaliza nome do serviço para comparação"""
        import re
        
        nome_normalizado = nome.upper().strip()
        
        # 1. Normalizar espaços múltiplos
        nome_normalizado = re.sub(r'\\s+', ' ', nome_normalizado)
        
        # 2. Normalizar códigos de aeroportos
        nome_normalizado = re.sub(r'RJ\\s*\\(GIG\\)', 'GIG', nome_normalizado)
        nome_normalizado = re.sub(r'RJ\\s*\\(SDU\\)', 'SDU', nome_normalizado) 
        nome_normalizado = re.sub(r'\\(GIG\\)', 'GIG', nome_normalizado)
        nome_normalizado = re.sub(r'\\(SDU\\)', 'SDU', nome_normalizado)
        
        # 3. Normalizar aeroportos
        nome_normalizado = re.sub(r'AEROPORTO\\s+INTER\\.\\s+GALEÃO', 'AEROPORTO GALEAO', nome_normalizado)
        nome_normalizado = re.sub(r'AEROPORTO\\s+SANTOS\\s+DUMONT', 'AEROPORTO SDU', nome_normalizado)
        
        # 4. Remover pontuações desnecessárias
        nome_normalizado = re.sub(r'[,\\.](?!\\d)', '', nome_normalizado)
        nome_normalizado = re.sub(r'\\s+', ' ', nome_normalizado)  # Limpar espaços novamente
        
        # 5. Normalizar variações específicas comuns
        nome_normalizado = re.sub(r'TRANSFER\\s+IN\\s+REGULAR', 'TRANSFER IN REGULAR', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\\s+OUT\\s+REGULAR', 'TRANSFER OUT REGULAR', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\\s+IN\\s+VEÍCULO\\s+PRIVATIVO', 'TRANSFER IN PRIVATIVO', nome_normalizado)
        nome_normalizado = re.sub(r'TRANSFER\\s+OUT\\s+VEÍCULO\\s+PRIVATIVO', 'TRANSFER OUT PRIVATIVO', nome_normalizado)
        
        return nome_normalizado.strip()'''

# Ler o arquivo
with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'r', encoding='utf-8') as f:
    conteudo = f.read()

# Substituir o método antigo pelo novo usando uma abordagem mais robusta
import re

# Padrão para encontrar o método e suas linhas
padrao = r'    def _normalizar_nome_servico\(self, nome\):\s*"""Normaliza nome do serviço para comparação"""\s*return nome\.upper\(\)\.strip\(\)'

conteudo_novo = re.sub(padrao, novo_metodo, conteudo)

# Verificar se a substituição foi feita
if conteudo_novo != conteudo:
    # Escrever de volta
    with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'w', encoding='utf-8') as f:
        f.write(conteudo_novo)
    print("✅ Método _normalizar_nome_servico atualizado com sucesso")
else:
    print("❌ Nenhuma substituição foi feita")
    
    # Vamos tentar uma abordagem linha por linha
    linhas = conteudo.split('\n')
    mudou = False
    
    i = 0
    while i < len(linhas):
        if 'def _normalizar_nome_servico(self, nome):' in linhas[i]:
            # Encontrou o método, vamos substituí-lo
            inicio = i
            
            # Pular as próximas linhas do método antigo
            i += 1
            while i < len(linhas) and (linhas[i].strip() == '"""Normaliza nome do serviço para comparação"""' or 
                                      linhas[i].strip() == 'return nome.upper().strip()' or
                                      linhas[i].strip() == ''):
                i += 1
            
            # Substituir as linhas
            linhas_novo_metodo = novo_metodo.split('\n')
            linhas[inicio:i] = linhas_novo_metodo
            mudou = True
            break
        i += 1
    
    if mudou:
        with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'w', encoding='utf-8') as f:
            f.write('\n'.join(linhas))
        print("✅ Método _normalizar_nome_servico atualizado linha por linha")
    else:
        print("❌ Não foi possível encontrar o método para substituir")