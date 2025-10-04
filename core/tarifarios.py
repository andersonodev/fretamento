"""
Tarifários de preços para o sistema de fretamento
Baseado nas tabelas originais do Google Apps Script
"""

# =================================================================
#      BASE DE DADOS DE PREÇOS (FIXA NO CÓDIGO)
# =================================================================

TARIFARIO_MOTORISTAS = {
    "Transfer In ou Out Sdu / Centro": 40.00,
    "Transfer In ou Out Sdu / Zona Sul ou São Conrado": 44.00,
    "Transfer In ou Out Sdu / Barra (Rio Design)": 81.00,
    "Transfer In ou Out Sdu / Recreio (Riocentro)": 81.00,
    "Transfer In ou Out Gig / Centro": 63.00,
    "Transfer In ou Out Gig / Zona Sul ou São Conrado": 77.00,
    "Transfer In ou Out Gig / Barra (Rio Design)": 103.00,
    "Transfer In ou Out Gig / Recreio (Riocentro)": 100.00,
    "Transfer In ou Out Gig ou Sdu / Niterói (Limite Icaraí)": 110.00,
    "Transfer In ou Out Petrópolis - Itaipava": 280.00,
    "Transfer In ou Out Le Canton": 305.00,
    "Transfer In ou Out Portobello - Club Med": 278.00,
    "Transfer In ou Out Vila Galé - Mercure - Centro": 400.00,
    "Transfer In ou Out Fasano Angra": 440.00,
    "Transfer In ou Out Paraty": 500.00,
    "Transfer In ou Out Búzios - Cabo Frio - Arraial": 400.00,
    "Transfer In ou Out Macaé": 444.00,
    "Transfer In ou Out Juiz de Fora": 600.00,
    "Disposição 04h": 170.00,
    "Disposição 06h": 209.00,
    "Disposição 08h": 283.00,
    "Disposição 10h": 304.00,
    "Hora extra": 46.00,
    "Tour Petrópolis ou Teresópolis": 326.00,
    "Tour Búzios - Cabo Frio ou Arraial": 568.00,
    "Tour em Angra dos Reis": 542.00,
    "By Night com/sem jantar (19h às 24h)": 170.00,
    "Ensaio Escola de Samba (21h às 02h)": 278.00,
    "Tour em Paraty": 700.00
}

TARIFARIO_JW = {
    "SDU / Zona Sul": {
        "Executivo": 229.00,
        "Van 15 lugares": 300.00,
        "Van 18 lugares": 389.00,
        "Micro": 826.00,
        "Ônibus": 983.00
    },
    "SDU / Zona Sul (mais de 1 hotel)": {
        "Executivo": None,
        "Van 15 lugares": 315.00,
        "Van 18 lugares": 400.00,
        "Micro": None,
        "Ônibus": None
    },
    "SDU / S.Conrado": {
        "Executivo": 229.00,
        "Van 15 lugares": 315.00,
        "Van 18 lugares": 407.00,
        "Micro": 826.00,
        "Ônibus": 986.00
    },
    "SDU / Barra + Recreio": {
        "Executivo": 253.00,
        "Van 15 lugares": 367.00,
        "Van 18 lugares": 477.00,
        "Micro": 989.00,
        "Ônibus": 1279.00
    },
    "AIRJ / Zona Sul": {
        "Executivo": 229.00,
        "Van 15 lugares": 310.00,
        "Van 18 lugares": 429.00,
        "Micro": 961.00,
        "Ônibus": 1144.00
    },
    "AIRJ / Zona Sul (Mais de 1 hotel)": {
        "Executivo": None,
        "Van 15 lugares": 322.00,
        "Van 18 lugares": 440.00,
        "Micro": None,
        "Ônibus": None
    },
    "AIRJ / S.Conrado": {
        "Executivo": 229.00,
        "Van 15 lugares": 367.00,
        "Van 18 lugares": 477.00,
        "Micro": 961.00,
        "Ônibus": 1144.00
    },
    "AIRJ / Barra + Recreio": {
        "Executivo": 256.00,
        "Van 15 lugares": 399.00,
        "Van 18 lugares": 517.00,
        "Micro": 1048.00,
        "Ônibus": 1279.00
    },
    "Cais do porto x Zona Sul": {
        "Executivo": 229.00,
        "Van 15 lugares": 329.00,
        "Van 18 lugares": 429.00,
        "Micro": 961.00,
        "Ônibus": 1144.00
    },
    "À disposição / Tour de 4 horas": {
        "Executivo": 472.00,
        "Van 15 lugares": 509.00,
        "Van 18 lugares": 662.00,
        "Micro": 1221.00,
        "Ônibus": 1542.00
    },
    "À disposição / Tour de 6 horas": {
        "Executivo": 683.00,
        "Van 15 lugares": 707.00,
        "Van 18 lugares": 884.00,
        "Micro": 1427.00,
        "Ônibus": 1835.00
    },
    "À disposição / Tour de 8 horas": {
        "Executivo": 861.00,
        "Van 15 lugares": 793.00,
        "Van 18 lugares": 1033.00,
        "Micro": 1626.00,
        "Ônibus": 2231.00
    },
    "Rio By Night - 4h": {
        "Executivo": 551.00,
        "Van 15 lugares": 525.00,
        "Van 18 lugares": 682.00,
        "Micro": 1294.00,
        "Ônibus": 1744.00
    },
    "Rio By Night - 6h": {
        "Executivo": 579.00,
        "Van 15 lugares": 629.00,
        "Van 18 lugares": 818.00,
        "Micro": 1362.00,
        "Ônibus": 1835.00
    },
    "Transfer Petrópolis": {
        "Executivo": 1021.00,
        "Van 15 lugares": 837.00,
        "Van 18 lugares": 1089.00,
        "Micro": 1949.00,
        "Ônibus": 2669.00
    },
    "Transfer Teresópolis": {
        "Executivo": 1003.00,
        "Van 15 lugares": 888.00,
        "Van 18 lugares": 1145.00,
        "Micro": 1921.00,
        "Ônibus": 2628.00
    },
    "Transfer Nova Friburgo": {
        "Executivo": 959.00,
        "Van 15 lugares": 888.00,
        "Van 18 lugares": 1145.00,
        "Micro": 2031.00,
        "Ônibus": 3140.00
    },
    "Transfer Itatiaia": {
        "Executivo": 1062.00,
        "Van 15 lugares": 970.00,
        "Van 18 lugares": 1245.00,
        "Micro": 2166.00,
        "Ônibus": 3026.00
    },
    "Transfer Itacuruçá": {
        "Executivo": 922.00,
        "Van 15 lugares": 793.00,
        "Van 18 lugares": 1033.00,
        "Micro": 1763.00,
        "Ônibus": 2690.00
    },
    "Transfer Club Med": {
        "Executivo": 1144.00,
        "Van 15 lugares": 793.00,
        "Van 18 lugares": 1033.00,
        "Micro": 2214.00,
        "Ônibus": 2751.00
    },
    "Transfer Angra dos Reis": {
        "Executivo": 1268.00,
        "Van 15 lugares": 1076.00,
        "Van 18 lugares": 1400.00,
        "Micro": 2637.00,
        "Ônibus": 3254.00
    },
    "Transfer Hotel do Frade": {
        "Executivo": 1198.00,
        "Van 15 lugares": 1198.00,
        "Van 18 lugares": 1558.00,
        "Micro": 2929.00,
        "Ônibus": 3464.00
    },
    "Transfer Hotel Vila Gale Angra": {
        "Executivo": 1268.00,
        "Van 15 lugares": 1167.00,
        "Van 18 lugares": 1517.00,
        "Micro": 2858.00,
        "Ônibus": 3524.00
    },
    "Transfer Macaé": {
        "Executivo": 1371.00,
        "Van 15 lugares": 1346.00,
        "Van 18 lugares": 1752.00,
        "Micro": 3296.00,
        "Ônibus": 4067.00
    },
    "Transfer Paraty": {
        "Executivo": 1732.00,
        "Van 15 lugares": 1572.00,
        "Van 18 lugares": 2044.00,
        "Micro": 3294.00,
        "Ônibus": 4198.00
    },
    "Transfer Búzios": {
        "Executivo": 1129.00,
        "Van 15 lugares": 1073.00,
        "Van 18 lugares": 1395.00,
        "Micro": 2798.00,
        "Ônibus": 3464.00
    },
    "Tour em Búzios": {
        "Executivo": 1341.00,
        "Van 15 lugares": 1332.00,
        "Van 18 lugares": 1733.00,
        "Micro": 3459.00,
        "Ônibus": 4037.00
    },
    "Tour em Angra": {
        "Executivo": 1295.00,
        "Van 15 lugares": 1272.00,
        "Van 18 lugares": 1654.00,
        "Micro": 3275.00,
        "Ônibus": 3732.00
    },
    "Tour em Paraty": {
        "Executivo": 1797.00,
        "Van 15 lugares": 1794.00,
        "Van 18 lugares": 2333.00,
        "Micro": 3275.00,
        "Ônibus": 4493.00
    },
    "Tour em Petrópolis": {
        "Executivo": 1097.00,
        "Van 15 lugares": 1016.00,
        "Van 18 lugares": 1324.00,
        "Micro": 2407.00,
        "Ônibus": 2818.00
    },
    "Sambódromo": {
        "Executivo": 1423.00,
        "Van 15 lugares": 1551.00,
        "Van 18 lugares": 2016.00,
        "Micro": 2242.00,
        "Ônibus": 3437.00
    },
    "Hora Extra": {
        "Executivo": 178.00,
        "Van 15 lugares": 147.00,
        "Van 18 lugares": 194.00,
        "Micro": 227.00,
        "Ônibus": 265.00
    },
    "Cancelamento no local": {
        "Executivo": 229.00,
        "Van 15 lugares": 310.00,
        "Van 18 lugares": 429.00,
        "Micro": 961.00,
        "Ônibus": 1144.00
    }
}

# Constantes auxiliares
CUSTO_DIARIO_VAN = 635.17
VEICULOS_DISPONIVEIS = ["Executivo", "Van 15 lugares", "Van 18 lugares", "Micro", "Ônibus"]


def buscar_preco_jw(chave_tarifario: str, veiculo: str) -> float:
    """
    Busca preço no tarifário JW
    
    Args:
        chave_tarifario: Chave do serviço no tarifário
        veiculo: Tipo de veículo
        
    Returns:
        Preço encontrado ou 0 se não encontrado
    """
    if chave_tarifario in TARIFARIO_JW:
        precos_servico = TARIFARIO_JW[chave_tarifario]
        if veiculo in precos_servico and precos_servico[veiculo] is not None:
            return float(precos_servico[veiculo])
    return 0.0


def buscar_preco_motoristas(chave_tarifario: str, numero_venda: str = "") -> float:
    """
    Busca preço no tarifário de motoristas
    Preço base é multiplicado pelo número de venda
    
    Args:
        chave_tarifario: Nome do serviço para busca
        numero_venda: Número da venda para usar como multiplicador
        
    Returns:
        Preço calculado (preço_base * numero_venda)
    """
    if chave_tarifario in TARIFARIO_MOTORISTAS:
        preco_base = TARIFARIO_MOTORISTAS[chave_tarifario]
        
        # Para serviços básicos, multiplica por número de venda
        try:
            # Tenta converter numero_venda para inteiro
            if numero_venda and numero_venda.strip():
                multiplicador = int(numero_venda.strip())
                return float(preco_base * multiplicador)
            else:
                # Se não tem número de venda, usa 1 como padrão
                return float(preco_base)
        except (ValueError, TypeError):
            # Se não conseguir converter, usa 1 como padrão
            return float(preco_base)
    
    return 0.0


def gerar_chave_tarifario(servico_obj) -> str:
    """
    Gera chave para busca no tarifário baseado no objeto serviço
    
    Args:
        servico_obj: Objeto Servico do Django
        
    Returns:
        Chave formatada para busca no tarifário
    """
    # Importação local para evitar circular import
    from core.models import Servico
    
    if not isinstance(servico_obj, Servico):
        return ""
    
    chave = ""
    
    if servico_obj.tipo == 'TRANSFER':
        # Monta chave para transfers
        if servico_obj.aeroporto == 'GIG':
            chave = "AIRJ / "
        elif servico_obj.aeroporto == 'SDU':
            chave = "SDU / "
        
        # Adiciona região
        if servico_obj.regiao == 'ZONA SUL':
            chave += "Zona Sul"
        elif servico_obj.regiao == 'SANTOS DUMONT':
            chave += "Zona Sul"  # SDU é tratado como Zona Sul
        elif servico_obj.regiao == 'BARRA':
            chave += "Barra + Recreio"
        elif servico_obj.regiao == 'CENTRO':
            chave += "Centro" if servico_obj.aeroporto == 'SDU' else "Zona Sul"
        
    elif servico_obj.tipo == 'DISPOSICAO':
        # Extrai horas da disposição
        import re
        match = re.search(r'(\d+)h', servico_obj.servico)
        if match:
            horas = match.group(1)
            chave = f"À disposição / Tour de {horas} horas"
        else:
            chave = "À disposição / Tour de 4 horas"  # Default
    
    elif servico_obj.tipo == 'TOUR':
        # Identifica tipo de tour
        servico_upper = servico_obj.servico.upper()
        if 'PETRÓPOLIS' in servico_upper or 'PETROPOLIS' in servico_upper:
            chave = "Tour em Petrópolis"
        elif 'BÚZIOS' in servico_upper or 'BUZIOS' in servico_upper:
            chave = "Tour em Búzios"
        elif 'ANGRA' in servico_upper:
            chave = "Tour em Angra"
        elif 'PARATY' in servico_upper:
            chave = "Tour em Paraty"
        elif 'BY NIGHT' in servico_upper:
            if '6h' in servico_upper or '6 h' in servico_upper:
                chave = "Rio By Night - 6h"
            else:
                chave = "Rio By Night - 4h"
    
    return chave


def calcular_veiculo_recomendado(pax: int) -> str:
    """
    Calcula veículo recomendado baseado no número de PAX
    
    Args:
        pax: Número de passageiros
        
    Returns:
        Tipo de veículo recomendado
    """
    if pax <= 3:
        return "Executivo"
    elif pax <= 11:
        return "Van 15 lugares"
    elif pax <= 14:
        return "Van 18 lugares"
    elif pax <= 26:
        return "Micro"
    else:
        return "Ônibus"


def calcular_preco_servico(servico_obj) -> tuple:
    """
    Calcula preço e veículo para um serviço usando busca inteligente
    
    Args:
        servico_obj: Objeto Servico do Django ou qualquer objeto com atributos servico, pax, numero_venda
        
    Returns:
        Tupla (veiculo_recomendado, preco_estimado)
    """
    # Importação local para evitar circular import
    from core.busca_inteligente_precos import BuscadorInteligentePrecosCodigoDoAnalista
    
    # Verificação mais flexível - apenas verifica se tem os atributos necessários
    if not hasattr(servico_obj, 'servico') or not hasattr(servico_obj, 'pax'):
        return ("Executivo", 0.0)
    
    pax = servico_obj.pax
    veiculo = calcular_veiculo_recomendado(pax)
    preco = 0.0
    
    # Usa busca inteligente avançada
    buscador = BuscadorInteligentePrecosCodigoDoAnalista()
    
    # Busca primeiro no tarifário JW com busca inteligente
    preco = buscador.buscar_preco_jw(
        nome_servico=servico_obj.servico,
        veiculo=veiculo
    )
    
    # Se não encontrou no JW com busca inteligente, tenta no tarifário de motoristas
    if preco == 0.0:
        numero_venda = getattr(servico_obj, 'numero_venda', 1)
        preco = buscador.buscar_preco_motoristas(
            nome_servico=servico_obj.servico,
            numero_venda=str(numero_venda)
        )
    
    # Se ainda não encontrou com busca inteligente, usa preço básico
    if preco == 0.0:
        precos_basicos = {
            "Executivo": 200.00,
            "Van 15 lugares": 300.00,
            "Van 18 lugares": 350.00,
            "Micro": 500.00,
            "Ônibus": 800.00
        }
        preco = precos_basicos.get(veiculo, 200.00)
    
    return (veiculo, float(preco))


def obter_estatisticas_tarifario() -> dict:
    """
    Retorna estatísticas dos tarifários
    
    Returns:
        Dicionário com estatísticas
    """
    return {
        'total_servicos_jw': len(TARIFARIO_JW),
        'total_servicos_motoristas': len(TARIFARIO_MOTORISTAS),
        'veiculos_disponiveis': VEICULOS_DISPONIVEIS,
        'custo_diario_van': CUSTO_DIARIO_VAN,
        'menor_preco_jw': min([
            min([v for v in servico.values() if v is not None])
            for servico in TARIFARIO_JW.values()
        ]),
        'maior_preco_jw': max([
            max([v for v in servico.values() if v is not None])
            for servico in TARIFARIO_JW.values()
        ]),
        'menor_preco_motoristas': min(TARIFARIO_MOTORISTAS.values()),
        'maior_preco_motoristas': max(TARIFARIO_MOTORISTAS.values()),
    }