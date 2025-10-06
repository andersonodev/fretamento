#!/usr/bin/env python3
"""
Versão melhorada dos métodos de agrupamento
"""

def normalizar_nome_servico_v2(nome):
    """Versão melhorada da normalização"""
    import re
    
    nome_normalizado = nome.upper().strip()
    
    # 1. Normalizar espaços múltiplos
    nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)
    
    # 2. Normalizar códigos de aeroportos
    nome_normalizado = re.sub(r'RJ\s*\(GIG\)', 'GIG', nome_normalizado)
    nome_normalizado = re.sub(r'RJ\s*\(SDU\)', 'SDU', nome_normalizado) 
    nome_normalizado = re.sub(r'\(GIG\)', 'GIG', nome_normalizado)
    nome_normalizado = re.sub(r'\(SDU\)', 'SDU', nome_normalizado)
    
    # 3. Normalizar aeroportos
    nome_normalizado = re.sub(r'AEROPORTO\s+INTER\.\s+GALEÃO', 'AEROPORTO GALEAO', nome_normalizado)
    nome_normalizado = re.sub(r'AEROPORTO\s+SANTOS\s+DUMONT', 'AEROPORTO SDU', nome_normalizado)
    
    # 4. Remover pontuações desnecessárias
    nome_normalizado = re.sub(r'[,\.](?!\d)', '', nome_normalizado)
    nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado)  # Limpar espaços novamente
    
    # 5. Normalizar variações específicas comuns
    nome_normalizado = re.sub(r'TRANSFER\s+IN\s+REGULAR', 'TRANSFER IN REGULAR', nome_normalizado)
    nome_normalizado = re.sub(r'TRANSFER\s+OUT\s+REGULAR', 'TRANSFER OUT REGULAR', nome_normalizado)
    nome_normalizado = re.sub(r'TRANSFER\s+IN\s+VEÍCULO\s+PRIVATIVO', 'TRANSFER IN PRIVATIVO', nome_normalizado)
    nome_normalizado = re.sub(r'TRANSFER\s+OUT\s+VEÍCULO\s+PRIVATIVO', 'TRANSFER OUT PRIVATIVO', nome_normalizado)
    
    return nome_normalizado.strip()

def calcular_diferenca_minutos(horario1, horario2):
    """Calcula diferença em minutos entre dois horários"""
    from datetime import datetime, time, date
    
    if not horario1 or not horario2:
        return float('inf')
    
    # Se forem strings, converter para time
    if isinstance(horario1, str):
        try:
            horario1 = datetime.strptime(horario1, '%H:%M:%S').time()
        except:
            try:
                horario1 = datetime.strptime(horario1, '%H:%M').time()
            except:
                return float('inf')
    
    if isinstance(horario2, str):
        try:
            horario2 = datetime.strptime(horario2, '%H:%M:%S').time()
        except:
            try:
                horario2 = datetime.strptime(horario2, '%H:%M').time()
            except:
                return float('inf')
    
    # Converter time para datetime para cálculo
    data_base = date.today()
    dt1 = datetime.combine(data_base, horario1)
    dt2 = datetime.combine(data_base, horario2)
    
    diferenca = abs((dt2 - dt1).total_seconds() / 60)
    return diferenca

def servicos_sao_compativeis_v2(servico1, servico2):
    """Versão melhorada da verificação de compatibilidade"""
    
    # 1. Mesmo nome de serviço normalizado e diferença de até 40 minutos
    nome1_norm = normalizar_nome_servico_v2(servico1.servico)
    nome2_norm = normalizar_nome_servico_v2(servico2.servico)
    
    print(f"DEBUG: Comparando serviços:")
    print(f"  Serviço 1: '{servico1.servico}' -> '{nome1_norm}'")
    print(f"  Serviço 2: '{servico2.servico}' -> '{nome2_norm}'")
    
    if nome1_norm == nome2_norm:
        diff_min = calcular_diferenca_minutos(servico1.horario, servico2.horario)
        print(f"  Nomes iguais! Diferença horário: {diff_min:.1f} min")
        if diff_min <= 40:  # Aumentado para 40 minutos
            print(f"  ✅ COMPATÍVEIS: Mesmo serviço dentro do intervalo de 40min")
            return True
        else:
            print(f"  ❌ Diferença de horário muito grande: {diff_min:.1f} min > 40")
    else:
        print(f"  ❌ Nomes diferentes")
    
    # 2. Transfers OUT regulares com mesmo local de pickup (≥ 4 PAX total)
    if ('TRANSFER OUT' in servico1.servico.upper() and 
        'TRANSFER OUT' in servico2.servico.upper() and
        'REGULAR' in servico1.servico.upper() and
        'REGULAR' in servico2.servico.upper()):
        
        pickup1 = getattr(servico1, 'local_pickup', '') or ''
        pickup2 = getattr(servico2, 'local_pickup', '') or ''
        
        if pickup1 == pickup2:
            total_pax = servico1.pax + servico2.pax
            print(f"  Transfer OUT regular - PAX total: {total_pax}")
            if total_pax >= 4:
                print(f"  ✅ COMPATÍVEIS: Transfer OUT regular com PAX suficiente")
                return True
    
    # 3. Tours em geral (mais flexível)
    if ('TOUR' in servico1.servico.upper() and 
        'TOUR' in servico2.servico.upper()):
        diff_min = calcular_diferenca_minutos(servico1.horario, servico2.horario)
        print(f"  Tours - Diferença horário: {diff_min:.1f} min")
        if diff_min <= 40:  # Aumentado para 40 minutos
            print(f"  ✅ COMPATÍVEIS: Tours dentro do intervalo")
            return True
    
    return False

if __name__ == "__main__":
    # Teste básico
    print("=== TESTE DA NORMALIZAÇÃO V2 ===")
    
    nomes_teste = [
        'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA ZONA SUL',
        'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL',
        'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL',
        'TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT RJ (SDU) PARA ZONA SUL',
    ]
    
    for nome in nomes_teste:
        normalizado = normalizar_nome_servico_v2(nome)
        print(f"'{nome}' -> '{normalizado}'")
    
    # Teste de comparação
    print("\n=== TESTE DE COMPARAÇÃO ===")
    nome1 = 'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA ZONA SUL'
    nome2 = 'TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL'
    
    norm1 = normalizar_nome_servico_v2(nome1)
    norm2 = normalizar_nome_servico_v2(nome2)
    
    print(f"Nome 1: '{nome1}'")
    print(f"Norm 1: '{norm1}'")
    print(f"Nome 2: '{nome2}'")
    print(f"Norm 2: '{norm2}'")
    print(f"Iguais: {norm1 == norm2}")