#!/usr/bin/env python3
"""
Aplicar a normalização melhorada no arquivo views.py - versão simplificada
"""

# Ler o arquivo
with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'r', encoding='utf-8') as f:
    linhas = f.readlines()

# Novo método como lista de linhas
novo_metodo_linhas = [
    '    def _normalizar_nome_servico(self, nome):\n',
    '        """Normaliza nome do serviço para comparação"""\n',
    '        import re\n',
    '        \n',
    '        nome_normalizado = nome.upper().strip()\n',
    '        \n',
    '        # 1. Normalizar espaços múltiplos\n',
    '        nome_normalizado = re.sub(r\'\\s+\', \' \', nome_normalizado)\n',
    '        \n',
    '        # 2. Normalizar códigos de aeroportos\n',
    '        nome_normalizado = re.sub(r\'RJ\\s*\\(GIG\\)\', \'GIG\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'RJ\\s*\\(SDU\\)\', \'SDU\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'\\(GIG\\)\', \'GIG\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'\\(SDU\\)\', \'SDU\', nome_normalizado)\n',
    '        \n',
    '        # 3. Normalizar aeroportos\n',
    '        nome_normalizado = re.sub(r\'AEROPORTO\\s+INTER\\.\\s+GALEÃO\', \'AEROPORTO GALEAO\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'AEROPORTO\\s+SANTOS\\s+DUMONT\', \'AEROPORTO SDU\', nome_normalizado)\n',
    '        \n',
    '        # 4. Remover pontuações desnecessárias\n',
    '        nome_normalizado = re.sub(r\'[,\\.](?!\\d)\', \'\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'\\s+\', \' \', nome_normalizado)  # Limpar espaços novamente\n',
    '        \n',
    '        # 5. Normalizar variações específicas comuns\n',
    '        nome_normalizado = re.sub(r\'TRANSFER\\s+IN\\s+REGULAR\', \'TRANSFER IN REGULAR\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'TRANSFER\\s+OUT\\s+REGULAR\', \'TRANSFER OUT REGULAR\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'TRANSFER\\s+IN\\s+VEÍCULO\\s+PRIVATIVO\', \'TRANSFER IN PRIVATIVO\', nome_normalizado)\n',
    '        nome_normalizado = re.sub(r\'TRANSFER\\s+OUT\\s+VEÍCULO\\s+PRIVATIVO\', \'TRANSFER OUT PRIVATIVO\', nome_normalizado)\n',
    '        \n',
    '        return nome_normalizado.strip()\n'
]

mudou = False
i = 0
while i < len(linhas):
    if 'def _normalizar_nome_servico(self, nome):' in linhas[i]:
        print(f"Encontrado método na linha {i+1}")
        inicio = i
        
        # Pular as próximas linhas do método antigo até encontrar o próximo def ou fim do método
        i += 1
        while i < len(linhas):
            linha_atual = linhas[i].strip()
            # Se encontrou uma nova função, parar
            if linha_atual.startswith('def ') and not linha_atual.startswith('def _normalizar_nome_servico'):
                break
            # Se encontrou return nome.upper().strip(), incluir e parar
            if 'return nome.upper().strip()' in linha_atual:
                i += 1
                break
            i += 1
        
        print(f"Substituindo linhas {inicio+1} a {i}")
        # Substituir as linhas
        linhas[inicio:i] = novo_metodo_linhas
        mudou = True
        break
    i += 1

if mudou:
    with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py', 'w', encoding='utf-8') as f:
        f.writelines(linhas)
    print("✅ Primeira instância do método _normalizar_nome_servico atualizada")
else:
    print("❌ Não foi possível encontrar o método")