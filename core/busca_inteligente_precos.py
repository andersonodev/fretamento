"""
Sistema inteligente de busca de preços
Implementa busca fuzzy e análise avançada de nomes de serviços
"""

import re
from difflib import SequenceMatcher
from typing import Dict, List, Tuple, Optional
from core.tarifarios import TARIFARIO_JW, TARIFARIO_MOTORISTAS


class BuscadorInteligentePrecosCodigoDoAnalista:
    """
    Sistema inteligente de busca de preços com múltiplos algoritmos de similaridade
    """
    
    def __init__(self):
        self.cache_similaridade = {}
        self.cache_busca = {}
        self.cache_normalizacao = {}
        # Importar os tarifários
        from core.tarifarios import TARIFARIO_JW, TARIFARIO_MOTORISTAS
        self.TARIFARIO_JW = TARIFARIO_JW
        self.TARIFARIO_MOTORISTAS = TARIFARIO_MOTORISTAS
    
    def normalizar_nome_servico(self, nome: str) -> str:
        """Normaliza nome do serviço para busca"""
        if nome in self.cache_normalizacao:
            return self.cache_normalizacao[nome]
        
        if not nome:
            return ""
        
        # Conversão para minúsculas e remoção de acentos
        nome_normalizado = nome.lower().strip()
        
        # Remove caracteres especiais mas mantém espaços
        nome_normalizado = re.sub(r'[^\w\s]', ' ', nome_normalizado)
        
        # Remove espaços múltiplos
        nome_normalizado = re.sub(r'\s+', ' ', nome_normalizado).strip()
        
        # Remove palavras comuns que não agregam valor
        palavras_ruido = {
            'de', 'da', 'do', 'para', 'em', 'no', 'na', 'com', 'por', 'sem',
            'transfer', 'transferencia', 'servico', 'viagem', 'ida', 'volta',
            'transporte', 'deslocamento', 'levar', 'buscar'
        }
        
        palavras = nome_normalizado.split()
        palavras_filtradas = [p for p in palavras if p not in palavras_ruido and len(p) > 1]
        
        resultado = ' '.join(palavras_filtradas)
        self.cache_normalizacao[nome] = resultado
        return resultado
    
    def gerar_variacoes_nome(self, nome: str) -> List[str]:
        """Gera variações do nome para busca mais flexível"""
        variacoes = [nome]
        
        # Adiciona variações com/sem palavras-chave
        variacoes_extras = [
            f"transfer {nome}",
            f"{nome} transfer",
            f"transferencia {nome}",
            f"{nome} transferencia",
            nome.replace("aeroporto", "apt"),
            nome.replace("apt", "aeroporto"),
            nome.replace("hotel", "htl"),
            nome.replace("htl", "hotel"),
            nome.replace("centro", "centro cidade"),
            nome.replace("centro cidade", "centro"),
        ]
        
        # Remove duplicatas e vazios
        variacoes.extend([v for v in variacoes_extras if v and v not in variacoes])
        
        return variacoes
    
    def calcular_similaridade(self, nome1: str, nome2: str) -> float:
        """Calcula similaridade entre dois nomes usando múltiplas métricas"""
        if not nome1 or not nome2:
            return 0.0
        
        # Normaliza ambos os nomes
        norm1 = self.normalizar_nome_servico(nome1)
        norm2 = self.normalizar_nome_servico(nome2)
        
        if norm1 == norm2:
            return 1.0
        
        # Múltiplas métricas de similaridade
        similaridades = []
        
        # 1. Similaridade de sequência
        similaridades.append(SequenceMatcher(None, norm1, norm2).ratio())
        
        # 2. Similaridade de palavras (Jaccard)
        palavras1 = set(norm1.split())
        palavras2 = set(norm2.split())
        if palavras1 or palavras2:
            intersecao = len(palavras1.intersection(palavras2))
            uniao = len(palavras1.union(palavras2))
            similaridades.append(intersecao / uniao if uniao > 0 else 0)
        
        # 3. Substring comum mais longa
        def lcs_length(s1, s2):
            m, n = len(s1), len(s2)
            dp = [[0] * (n + 1) for _ in range(m + 1)]
            for i in range(1, m + 1):
                for j in range(1, n + 1):
                    if s1[i-1] == s2[j-1]:
                        dp[i][j] = dp[i-1][j-1] + 1
                    else:
                        dp[i][j] = max(dp[i-1][j], dp[i][j-1])
            return dp[m][n]
        
        lcs_len = lcs_length(norm1, norm2)
        max_len = max(len(norm1), len(norm2))
        if max_len > 0:
            similaridades.append(lcs_len / max_len)
        
        # 4. Palavras-chave importantes
        palavras_importantes = {
            'aeroporto', 'apt', 'hotel', 'centro', 'praia', 'shopping',
            'rodoviaria', 'porto', 'estacao', 'terminal', 'cidade'
        }
        
        importantes1 = {p for p in palavras1 if p in palavras_importantes}
        importantes2 = {p for p in palavras2 if p in palavras_importantes}
        
        if importantes1 or importantes2:
            match_importantes = len(importantes1.intersection(importantes2))
            total_importantes = len(importantes1.union(importantes2))
            if total_importantes > 0:
                similaridades.append(match_importantes / total_importantes)
        
        # Retorna a média ponderada das similaridades
        if similaridades:
            return sum(similaridades) / len(similaridades)
        
        return 0.0
    
    def buscar_melhor_match_tarifario(self, nome_servico: str, tarifario: Dict[str, float], 
                                     threshold: float = 0.3) -> Tuple[Optional[str], float, float]:
        """
        Busca o melhor match no tarifário usando similaridade
        
        Returns:
            Tuple (chave_encontrada, preco, similaridade)
        """
        cache_key = f"{nome_servico}_{id(tarifario)}_{threshold}"
        if cache_key in self.cache_busca:
            return self.cache_busca[cache_key]
        
        melhor_match = None
        melhor_similaridade = 0.0
        melhor_preco = 0.0
        
        # Gera variações do nome de entrada
        variacoes_entrada = self.gerar_variacoes_nome(nome_servico)
        
        # Busca em todas as chaves do tarifário
        for chave_tarifario, preco in tarifario.items():
            # Testa cada variação contra a chave do tarifário
            for variacao in variacoes_entrada:
                similaridade = self.calcular_similaridade(variacao, chave_tarifario)
                
                if similaridade > melhor_similaridade and similaridade >= threshold:
                    melhor_similaridade = similaridade
                    melhor_match = chave_tarifario
                    melhor_preco = preco
        
        resultado = (melhor_match, melhor_preco, melhor_similaridade)
        self.cache_busca[cache_key] = resultado
        return resultado
    
    def buscar_preco_inteligente(self, nome_servico: str, pax: int = 1, 
                               numero_venda: str = "") -> Tuple[str, float, str]:
        """
        Busca inteligente de preço em ambos os tarifários
        
        Returns:
            Tuple (veiculo, preco, fonte)
        """
        if not nome_servico:
            return ("Executivo", 0.0, "não encontrado")
        
        # 1. Busca no TARIFARIO_JW primeiro (mais específico e confiável)
        chave_jw, preco_jw, sim_jw = self.buscar_melhor_match_tarifario(
            nome_servico, self.TARIFARIO_JW, threshold=0.4
        )
        
        if chave_jw and sim_jw > 0.6:  # Alta confiança no JW
            from core.tarifarios import calcular_veiculo_recomendado
            veiculo = calcular_veiculo_recomendado(pax)
            # JW tem preços por veículo, busca o preço correto
            if isinstance(preco_jw, dict):
                preco_final = preco_jw.get(veiculo, preco_jw.get("Executivo", 0))
            else:
                preco_final = preco_jw
            return (veiculo, float(preco_final), f"JW (sim: {sim_jw:.2f})")
        
        # 2. Busca no TARIFARIO_MOTORISTAS (com lógica corrigida de multiplicador)
        chave_mot, preco_mot, sim_mot = self.buscar_melhor_match_tarifario(
            nome_servico, self.TARIFARIO_MOTORISTAS, threshold=0.25  # Threshold mais baixo
        )
        
        if chave_mot and sim_mot > 0.25:  # Threshold de confiança mais baixo
            from core.tarifarios import calcular_veiculo_recomendado
            veiculo = calcular_veiculo_recomendado(pax)
            
            # CORREÇÃO: Não usar número de venda como multiplicador direto
            # Número de venda é apenas um identificador, não um fator de preço
            # O preço do tarifário motoristas já é um preço fixo por serviço
            preco_final = float(preco_mot)
            
            return (veiculo, preco_final, f"Motoristas (sim: {sim_mot:.2f})")
        
        # 3. Busca com threshold mais baixo no JW para matches parciais
        if chave_jw and sim_jw > 0.4:  # Threshold menor para casos intermediários
            from core.tarifarios import calcular_veiculo_recomendado
            veiculo = calcular_veiculo_recomendado(pax)
            if isinstance(preco_jw, dict):
                preco_final = preco_jw.get(veiculo, preco_jw.get("Executivo", 0))
            else:
                preco_final = preco_jw
            
            if preco_final > 0:
                return (veiculo, float(preco_final), f"JW-parcial (sim: {sim_jw:.2f})")
        
        # 4. Se não encontrou nada, usa preço padrão baseado no veículo e PAX
        from core.tarifarios import calcular_veiculo_recomendado
        veiculo = calcular_veiculo_recomendado(pax)
        
        # Preços padrão baseados no veículo e ajustados por PAX
        precos_base = {
            "Executivo": 200.0,
            "Van 15 lugares": 300.0,
            "Van 18 lugares": 350.0,
            "Micro": 500.0,
            "Ônibus": 800.0
        }
        
        preco_base = precos_base.get(veiculo, 200.0)
        # Ajuste por PAX (pequeno fator para refletir complexidade)
        ajuste_pax = 1.0 + (pax - 1) * 0.1  # 10% a mais por PAX adicional
        preco_final = preco_base * min(ajuste_pax, 2.0)  # Máximo 2x o preço base
        
        return (veiculo, preco_final, f"padrão (PAX: {pax})")
    
    def buscar_preco_jw(self, nome_servico: str, veiculo: str = "Executivo") -> float:
        """
        Busca específica no tarifário JW
        
        Args:
            nome_servico: Nome do serviço a buscar
            veiculo: Tipo de veículo
            
        Returns:
            Preço encontrado ou 0.0 se não encontrado
        """
        chave, preco, similaridade = self.buscar_melhor_match_tarifario(
            nome_servico, self.TARIFARIO_JW, threshold=0.4
        )
        
        if chave and similaridade > 0.6:
            if isinstance(preco, dict):
                return float(preco.get(veiculo, preco.get("Executivo", 0)))
            else:
                return float(preco)
        
        return 0.0
    
    def buscar_preco_motoristas(self, nome_servico: str, numero_venda: str = "1") -> float:
        """
        Busca específica no tarifário de motoristas
        
        Args:
            nome_servico: Nome do serviço a buscar
            numero_venda: Número de vendas (usado apenas como referência, não multiplicador)
            
        Returns:
            Preço encontrado ou 0.0 se não encontrado
        """
        chave, preco, similaridade = self.buscar_melhor_match_tarifario(
            nome_servico, self.TARIFARIO_MOTORISTAS, threshold=0.2  # Threshold mais baixo
        )
        
        if chave and similaridade > 0.4:  # Threshold de confiança
            # CORREÇÃO: Não usar número de venda como multiplicador
            # O preço já está correto no tarifário
            return float(preco)
        
        return 0.0


# Instância global do buscador
buscador_inteligente = BuscadorInteligentePrecosCodigoDoAnalista()

# === DADOS HISTÓRICOS INTEGRADOS ===
# Gerado automaticamente em 07/10/2025 16:56:17

PADROES_HISTORICOS = {
  "TRANSFER": {
    "count": 152,
    "preco_medio": 110.36348684210526,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 2.901315789473684,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "REGULAR": {
    "count": 449,
    "preco_medio": 142.5673719376392,
    "preco_min": 40.0,
    "preco_max": 793.0,
    "pax_medio": 4.2071269487750556,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      }
    ]
  },
  "AEROPORTO": {
    "count": 148,
    "preco_medio": 106.40371621621621,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 2.8175675675675675,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "SANTOS": {
    "count": 46,
    "preco_medio": 90.21739130434783,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 3.369565217391304,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 44.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO SANTOS DUMONT RJ (SDU) PARA ZONA SUL"
      },
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      }
    ]
  },
  "DUMONT": {
    "count": 46,
    "preco_medio": 90.21739130434783,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 3.369565217391304,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 44.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO SANTOS DUMONT RJ (SDU) PARA ZONA SUL"
      },
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      }
    ]
  },
  "SDU": {
    "count": 213,
    "preco_medio": 114.97300469483568,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 4.046948356807512,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 44.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO SANTOS DUMONT RJ (SDU) PARA ZONA SUL"
      },
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      }
    ]
  },
  "ZONA": {
    "count": 137,
    "preco_medio": 109.51277372262774,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 3.3284671532846715,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "SUL": {
    "count": 220,
    "preco_medio": 130.16704545454544,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 3.709090909090909,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "TRANSFER IN": {
    "count": 73,
    "preco_medio": 117.63356164383562,
    "preco_min": 40.0,
    "preco_max": 1020.0,
    "pax_medio": 3.1232876712328768,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      },
      {
        "preco": 77.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      }
    ]
  },
  "IN REGULAR": {
    "count": 176,
    "preco_medio": 140.96022727272728,
    "preco_min": 40.0,
    "preco_max": 400.0,
    "pax_medio": 4.3352272727272725,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      },
      {
        "preco": 77.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      }
    ]
  },
  "REGULAR AEROPORTO": {
    "count": 30,
    "preco_medio": 97.68333333333334,
    "preco_min": 40.0,
    "preco_max": 400.0,
    "pax_medio": 2.4,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA ZONA SUL RJ"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      },
      {
        "preco": 77.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO (GIG) PARA ZONA SUL"
      }
    ]
  },
  "OUT": {
    "count": 584,
    "preco_medio": 161.85530821917808,
    "preco_min": 40.0,
    "preco_max": 509.0,
    "pax_medio": 4.0256849315068495,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "BÚZIOS": {
    "count": 12,
    "preco_medio": 182.66666666666666,
    "preco_min": 63.0,
    "preco_max": 400.0,
    "pax_medio": 2.0833333333333335,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO (GIG) / BÚZIOS"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "ARMAÇÃO": {
    "count": 5,
    "preco_medio": 205.5,
    "preco_min": 63.0,
    "preco_max": 400.0,
    "pax_medio": 2.6,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      },
      {
        "preco": 400.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "JOÃO": {
    "count": 5,
    "preco_medio": 205.5,
    "preco_min": 63.0,
    "preco_max": 400.0,
    "pax_medio": 2.6,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      },
      {
        "preco": 400.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "FERNANDES": {
    "count": 5,
    "preco_medio": 205.5,
    "preco_min": 63.0,
    "preco_max": 400.0,
    "pax_medio": 2.6,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      },
      {
        "preco": 400.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "CENTRO": {
    "count": 68,
    "preco_medio": 116.32352941176471,
    "preco_min": 40.0,
    "preco_max": 400.0,
    "pax_medio": 3.5588235294117645,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "GERIBÁ": {
    "count": 5,
    "preco_medio": 205.5,
    "preco_min": 63.0,
    "preco_max": 400.0,
    "pax_medio": 2.6,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 400.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      },
      {
        "preco": 400.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ)"
      }
    ]
  },
  "INTER": {
    "count": 104,
    "preco_medio": 112.87740384615384,
    "preco_min": 40.0,
    "preco_max": 400.0,
    "pax_medio": 2.5576923076923075,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "GALEÃO": {
    "count": 104,
    "preco_medio": 112.87740384615384,
    "preco_min": 40.0,
    "preco_max": 400.0,
    "pax_medio": 2.5576923076923075,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "GIG": {
    "count": 835,
    "preco_medio": 185.2125748502994,
    "preco_min": 40.0,
    "preco_max": 509.0,
    "pax_medio": 4.174850299401197,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "TRANSFER OUT": {
    "count": 73,
    "preco_medio": 96.15068493150685,
    "preco_min": 44.0,
    "preco_max": 240.0,
    "pax_medio": 2.5342465753424657,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "OUT REGULAR": {
    "count": 246,
    "preco_medio": 125.58028455284553,
    "preco_min": 40.0,
    "preco_max": 310.0,
    "pax_medio": 3.967479674796748,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 206.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Barra x GIG"
      }
    ]
  },
  "REGULAR BÚZIOS": {
    "count": 2,
    "preco_medio": 63.0,
    "preco_min": 63.0,
    "preco_max": 63.0,
    "pax_medio": 2.5,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 63.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BÚZIOS (ARMAÇÃO, JOÃO FERNANDES, CENTRO, GERIBÁ) PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "VEÍCULO": {
    "count": 79,
    "preco_medio": 130.80696202531647,
    "preco_min": 44.0,
    "preco_max": 1087.0,
    "pax_medio": 3.3164556962025316,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 7,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "PRIVATIVO": {
    "count": 611,
    "preco_medio": 203.24345335515548,
    "preco_min": 44.0,
    "preco_max": 1020.0,
    "pax_medio": 4.2078559738134205,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 7,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "VEÍCULO PRIVATIVO": {
    "count": 76,
    "preco_medio": 116.04276315789474,
    "preco_min": 44.0,
    "preco_max": 1020.0,
    "pax_medio": 3.289473684210526,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 7,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "PRIVATIVO ZONA": {
    "count": 36,
    "preco_medio": 98.76388888888889,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 3.0,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 77.0,
        "pax": 7,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "IN PRIVATIVO": {
    "count": 232,
    "preco_medio": 227.58189655172413,
    "preco_min": 44.0,
    "preco_max": 509.0,
    "pax_medio": 4.452586206896552,
    "exemplos": [
      {
        "preco": 390.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN PRIVATIVO AEROPORTO INTER. GALEÃO RJ (GIG) PARA Z. SUL"
      },
      {
        "preco": 310.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "ZONA SUL",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gig x Zona sul"
      },
      {
        "preco": 362.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Privativo GIG x Barra"
      }
    ]
  },
  "PRIVATIVO AEROPORTO": {
    "count": 43,
    "preco_medio": 131.55232558139534,
    "preco_min": 44.0,
    "preco_max": 1020.0,
    "pax_medio": 3.627906976744186,
    "exemplos": [
      {
        "preco": 390.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN PRIVATIVO AEROPORTO INTER. GALEÃO RJ (GIG) PARA Z. SUL"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO (GIG) / BÚZIOS"
      },
      {
        "preco": 77.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO RJ (GIG) / ZONA SUL"
      }
    ]
  },
  "BARRA": {
    "count": 186,
    "preco_medio": 227.2311827956989,
    "preco_min": 81.0,
    "preco_max": 399.0,
    "pax_medio": 4.198924731182796,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 206.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Barra x GIG"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO (GIG) PARA BARRA DA TIJUCA"
      }
    ]
  },
  "TIJUCA": {
    "count": 22,
    "preco_medio": 144.5,
    "preco_min": 81.0,
    "preco_max": 240.0,
    "pax_medio": 2.227272727272727,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO (GIG) PARA BARRA DA TIJUCA"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN VEÍCULO PRIVATIVO AEROPORTO INTER. GALEÃO (GIG) PARA BARRA DA TIJUCA"
      }
    ]
  },
  "RECREIO": {
    "count": 13,
    "preco_medio": 108.88461538461539,
    "preco_min": 81.0,
    "preco_max": 220.0,
    "pax_medio": 2.3076923076923075,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      }
    ]
  },
  "DOS": {
    "count": 5,
    "preco_medio": 141.2,
    "preco_min": 101.5,
    "preco_max": 220.0,
    "pax_medio": 3.2,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      }
    ]
  },
  "BANDEIRANTES": {
    "count": 5,
    "preco_medio": 141.2,
    "preco_min": 101.5,
    "preco_max": 220.0,
    "pax_medio": 3.2,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO INTER. GALEÃO RJ (GIG) PARA BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES"
      }
    ]
  },
  "REGULAR BARRA": {
    "count": 23,
    "preco_medio": 146.77173913043478,
    "preco_min": 81.0,
    "preco_max": 309.0,
    "pax_medio": 3.347826086956522,
    "exemplos": [
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR BARRA DA TIJUCA OU RECREIO DOS BANDEIRANTES PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      },
      {
        "preco": 206.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Barra x GIG"
      },
      {
        "preco": 81.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Regular Barra x Sdu"
      }
    ]
  },
  "HOTÉIS": {
    "count": 9,
    "preco_medio": 71.88888888888889,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.2222222222222223,
    "exemplos": [
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER IN REGULAR AEROPORTO SANTOS DUMONT (SDU) PARA HOTÉIS CENTRO"
      }
    ]
  },
  "ZSUL": {
    "count": 427,
    "preco_medio": 177.10889929742387,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 4.423887587822014,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZSul x Gig"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Zsul x Gig"
      }
    ]
  },
  "OUT PRIVATIVO": {
    "count": 288,
    "preco_medio": 201.67013888888889,
    "preco_min": 44.0,
    "preco_max": 509.0,
    "pax_medio": 4.277777777777778,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x GIG"
      },
      {
        "preco": 77.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZS x GIG"
      },
      {
        "preco": 310.0,
        "pax": 8,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZS x GIG"
      }
    ]
  },
  "PRIVATIVO ZSUL": {
    "count": 152,
    "preco_medio": 201.20394736842104,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 4.4868421052631575,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x GIG"
      },
      {
        "preco": 310.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x Gig"
      },
      {
        "preco": 77.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x Gig"
      }
    ]
  },
  "PRIVATIVO GIG": {
    "count": 188,
    "preco_medio": 229.67287234042553,
    "preco_min": 63.0,
    "preco_max": 509.0,
    "pax_medio": 4.4787234042553195,
    "exemplos": [
      {
        "preco": 310.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "ZONA SUL",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gig x Zona sul"
      },
      {
        "preco": 362.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Privativo GIG x Barra"
      },
      {
        "preco": 310.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gig x ZSul"
      }
    ]
  },
  "REGULAR GIG": {
    "count": 93,
    "preco_medio": 172.2688172043011,
    "preco_min": 63.0,
    "preco_max": 362.0,
    "pax_medio": 4.989247311827957,
    "exemplos": [
      {
        "preco": 308.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Regular Gig x Z Sul"
      },
      {
        "preco": 206.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Regular GIG x Barra"
      },
      {
        "preco": 154.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Regular GIG x ZS"
      }
    ]
  },
  "PRIVATIVO ZS": {
    "count": 40,
    "preco_medio": 156.9,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 3.675,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZS x GIG"
      },
      {
        "preco": 310.0,
        "pax": 8,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZS x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZS x GIG"
      }
    ]
  },
  "REGULAR ZSUL": {
    "count": 99,
    "preco_medio": 133.77777777777777,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 4.555555555555555,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZSul x Gig"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Zsul x Gig"
      },
      {
        "preco": 154.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZSul x Gig"
      }
    ]
  },
  "PRIVATIVO SDU": {
    "count": 25,
    "preco_medio": 204.0,
    "preco_min": 44.0,
    "preco_max": 367.0,
    "pax_medio": 4.56,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "IN Privativo SDU x ZS"
      },
      {
        "preco": 44.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Privativo SDU x Copa"
      },
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Privativo SDU x ZSul"
      }
    ]
  },
  "PRIVATIVO BARRA": {
    "count": 55,
    "preco_medio": 270.5090909090909,
    "preco_min": 101.5,
    "preco_max": 399.0,
    "pax_medio": 4.763636363636364,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO BARRA DA TIJUCA PARA AEROPORTO INTER. GALEÃO (GIG)"
      },
      {
        "preco": 103.0,
        "pax": 3,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barra x GIG"
      },
      {
        "preco": 362.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barra x Gig"
      }
    ]
  },
  "REGULAR ZONA": {
    "count": 37,
    "preco_medio": 96.97297297297297,
    "preco_min": 44.0,
    "preco_max": 231.0,
    "pax_medio": 2.5945945945945947,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR ZONA SUL PARA AEROPORTO SANTOS DUMONT RJ (SDU)"
      },
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR ZONA SUL PARA AEROPORTO SANTOS DUMONT RJ (SDU)"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR ZONA SUL PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "REGULAR ZS": {
    "count": 34,
    "preco_medio": 139.47058823529412,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 4.5588235294117645,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZS x GIG"
      },
      {
        "preco": 154.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZS x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular ZS x GIG"
      }
    ]
  },
  "TOUR": {
    "count": 58,
    "preco_medio": 479.33051724137925,
    "preco_min": 40.0,
    "preco_max": 793.0,
    "pax_medio": 5.793103448275862,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "04HRS": {
    "count": 17,
    "preco_medio": 368.2352941176471,
    "preco_min": 120.0,
    "preco_max": 509.0,
    "pax_medio": 5.294117647058823,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 13,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Van disposisção 04hrs"
      }
    ]
  },
  "CORCOVADO": {
    "count": 8,
    "preco_medio": 424.4375,
    "preco_min": 178.5,
    "preco_max": 600.0,
    "pax_medio": 7.875,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "TOUR DE": {
    "count": 30,
    "preco_medio": 592.439,
    "preco_min": 170.0,
    "preco_max": 793.0,
    "pax_medio": 6.3,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 793.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR DE 08HRS"
      }
    ]
  },
  "CORCOVADO REGULAR": {
    "count": 2,
    "preco_medio": 509.0,
    "preco_min": 509.0,
    "preco_max": 509.0,
    "pax_medio": 10.0,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      },
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs Corcovado - Regular"
      }
    ]
  },
  "DISPOSIÇÃO": {
    "count": 8,
    "preco_medio": 542.875,
    "preco_min": 101.5,
    "preco_max": 1381.0,
    "pax_medio": 6.125,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "DISPOSICAO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 4 horas"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 06h"
      },
      {
        "preco": 1381.0,
        "pax": 5,
        "tipo": "DISPOSICAO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 12hs"
      }
    ]
  },
  "HORAS": {
    "count": 6,
    "preco_medio": 565.8333333333334,
    "preco_min": 170.0,
    "preco_max": 793.0,
    "pax_medio": 5.833333333333333,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 10,
        "tipo": "DISPOSICAO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 4 horas"
      },
      {
        "preco": 509.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disp. 4 Horas"
      },
      {
        "preco": 170.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disp. 4 horas - Sedan"
      }
    ]
  },
  "REGULAR CENTRO": {
    "count": 25,
    "preco_medio": 91.28,
    "preco_min": 40.0,
    "preco_max": 310.0,
    "pax_medio": 3.16,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Centro x Gig"
      },
      {
        "preco": 40.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Regular Centro x SDU"
      },
      {
        "preco": 63.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT REGULAR CENTRO RJ PARA AEROPORTO INTER. GALEÃO RJ (GIG)"
      }
    ]
  },
  "REGULAR SDU": {
    "count": 47,
    "preco_medio": 105.32978723404256,
    "preco_min": 40.0,
    "preco_max": 300.0,
    "pax_medio": 4.23404255319149,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Regular SDU x ZS"
      },
      {
        "preco": 44.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Regular SDU x ZSul"
      },
      {
        "preco": 81.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Regular SDU X Barra "
      }
    ]
  },
  "NOVO": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      }
    ]
  },
  "NOVO TRANSFER": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      }
    ]
  },
  "TRANSFER REGULAR": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      }
    ]
  },
  "REGULAR IN": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "NOVO: TRANSFER REGULAR IN AEROPORTO INTER. GALEÃO RJ (GIG) OU SANTOS DUMONT (SDU) RJ PARA ZONA SUL OU CENTRO"
      }
    ]
  },
  "COPA": {
    "count": 7,
    "preco_medio": 153.14285714285714,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 3.7142857142857144,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Privativo SDU x Copa"
      },
      {
        "preco": 88.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Regular Copa x SDU"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Copa x Gig"
      }
    ]
  },
  "DISP": {
    "count": 3,
    "preco_medio": 490.6666666666667,
    "preco_min": 170.0,
    "preco_max": 793.0,
    "pax_medio": 3.6666666666666665,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disp. 4 Horas"
      },
      {
        "preco": 170.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disp. 4 horas - Sedan"
      },
      {
        "preco": 793.0,
        "pax": 5,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Privativo Disp. 8 Horas"
      }
    ]
  },
  "PRIVATIVO Z": {
    "count": 31,
    "preco_medio": 138.96774193548387,
    "preco_min": 77.0,
    "preco_max": 310.0,
    "pax_medio": 3.3225806451612905,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Z. Sul X GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Z. Sul X GIG"
      },
      {
        "preco": 310.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Z. Sul x GIG"
      }
    ]
  },
  "SEDANS": {
    "count": 14,
    "preco_medio": 176.78571428571428,
    "preco_min": 88.0,
    "preco_max": 308.0,
    "pax_medio": 5.142857142857143,
    "exemplos": [
      {
        "preco": 231.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Regular GIG x Z. Sul - 3 Sedans"
      },
      {
        "preco": 154.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Z. Sul x GIG - 02 sedans"
      },
      {
        "preco": 154.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gig x Z Sul 02 sedans"
      }
    ]
  },
  "DIA": {
    "count": 3,
    "preco_medio": 363.3333333333333,
    "preco_min": 220.0,
    "preco_max": 570.0,
    "pax_medio": 7.333333333333333,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR UM DIA NO RIO: PÃO DE AÇÚCAR, CORCOVADO C/ SUBIDA EM VAN, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "RIO": {
    "count": 7,
    "preco_medio": 258.57142857142856,
    "preco_min": 40.0,
    "preco_max": 570.0,
    "pax_medio": 5.142857142857143,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "PÃO": {
    "count": 6,
    "preco_medio": 306.4166666666667,
    "preco_min": 170.0,
    "preco_max": 570.0,
    "pax_medio": 5.666666666666667,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Pão e praias s/ ingressos"
      }
    ]
  },
  "AÇÚCAR": {
    "count": 5,
    "preco_medio": 333.7,
    "preco_min": 178.5,
    "preco_max": 570.0,
    "pax_medio": 6.4,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      }
    ]
  },
  "TREM": {
    "count": 4,
    "preco_medio": 412.125,
    "preco_min": 178.5,
    "preco_max": 600.0,
    "pax_medio": 7.5,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "INGRESSO TREM DO CORCOVADO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "CITY": {
    "count": 3,
    "preco_medio": 363.3333333333333,
    "preco_min": 220.0,
    "preco_max": 570.0,
    "pax_medio": 7.333333333333333,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR UM DIA NO RIO: PÃO DE AÇÚCAR, CORCOVADO C/ SUBIDA EM VAN, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "ALMOÇO": {
    "count": 4,
    "preco_medio": 470.75,
    "preco_min": 220.0,
    "preco_max": 793.0,
    "pax_medio": 8.0,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 793.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular UDR em Van + Almoço"
      }
    ]
  },
  "RIO REGULAR": {
    "count": 2,
    "preco_medio": 435.0,
    "preco_min": 300.0,
    "preco_max": 570.0,
    "pax_medio": 10.0,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "REGULAR PÃO": {
    "count": 3,
    "preco_medio": 346.6666666666667,
    "preco_min": 170.0,
    "preco_max": 570.0,
    "pax_medio": 7.333333333333333,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Pão e praias s/ ingressos"
      }
    ]
  },
  "CITY TOUR": {
    "count": 3,
    "preco_medio": 363.3333333333333,
    "preco_min": 220.0,
    "preco_max": 570.0,
    "pax_medio": 7.333333333333333,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR UM DIA NO RIO: PÃO DE AÇÚCAR, CORCOVADO C/ SUBIDA EM VAN, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "TOUR E": {
    "count": 3,
    "preco_medio": 363.3333333333333,
    "preco_min": 220.0,
    "preco_max": 570.0,
    "pax_medio": 7.333333333333333,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 570.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "UM DIA NO RIO REGULAR: PÃO DE AÇÚCAR, CORCOVADO EM TREM, CITY TOUR E ALMOÇO"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR UM DIA NO RIO: PÃO DE AÇÚCAR, CORCOVADO C/ SUBIDA EM VAN, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "SEDAN": {
    "count": 5,
    "preco_medio": 170.0,
    "preco_min": 170.0,
    "preco_max": 170.0,
    "pax_medio": 1.8,
    "exemplos": [
      {
        "preco": 170.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disp. 4 horas - Sedan"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs - sedan privativo"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 04hrs sedan priv"
      }
    ]
  },
  "REGULAR Z": {
    "count": 24,
    "preco_medio": 137.04166666666666,
    "preco_min": 44.0,
    "preco_max": 310.0,
    "pax_medio": 4.458333333333333,
    "exemplos": [
      {
        "preco": 154.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Z. Sul X GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Z Sul x Gig"
      },
      {
        "preco": 310.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular Z Sul x Gig"
      }
    ]
  },
  "VAN": {
    "count": 3,
    "preco_medio": 507.3333333333333,
    "preco_min": 220.0,
    "preco_max": 793.0,
    "pax_medio": 8.333333333333334,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 13,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Van disposisção 04hrs"
      },
      {
        "preco": 793.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular UDR em Van + Almoço"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR UM DIA NO RIO: PÃO DE AÇÚCAR, CORCOVADO C/ SUBIDA EM VAN, CITY TOUR E ALMOÇO"
      }
    ]
  },
  "INGRESSO": {
    "count": 4,
    "preco_medio": 279.625,
    "preco_min": 170.0,
    "preco_max": 600.0,
    "pax_medio": 3.5,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "INGRESSO TREM DO CORCOVADO"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botânico s/ ingresso"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular JB s/ ingresso"
      }
    ]
  },
  "HERANÇAS": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      }
    ]
  },
  "EUROPEIAS": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      }
    ]
  },
  "PELO": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      }
    ]
  },
  "TOUR REGULAR": {
    "count": 15,
    "preco_medio": 345.43333333333334,
    "preco_min": 40.0,
    "preco_max": 793.0,
    "pax_medio": 5.266666666666667,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Pão e praias s/ ingressos"
      },
      {
        "preco": 793.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular UDR em Van + Almoço"
      }
    ]
  },
  "REGULAR HERANÇAS": {
    "count": 2,
    "preco_medio": 70.75,
    "preco_min": 40.0,
    "preco_max": 101.5,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      },
      {
        "preco": 40.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR HERANÇAS EUROPEIAS PELO CENTRO DO RIO"
      }
    ]
  },
  "INGRESSOS": {
    "count": 2,
    "preco_medio": 339.5,
    "preco_min": 170.0,
    "preco_max": 509.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Pão e praias s/ ingressos"
      },
      {
        "preco": 509.0,
        "pax": 8,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botanico s/ ingressos"
      }
    ]
  },
  "VISITA": {
    "count": 2,
    "preco_medio": 289.25,
    "preco_min": 178.5,
    "preco_max": 400.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      },
      {
        "preco": 400.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      }
    ]
  },
  "CATEDRAL": {
    "count": 2,
    "preco_medio": 289.25,
    "preco_min": 178.5,
    "preco_max": 400.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      },
      {
        "preco": 400.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      }
    ]
  },
  "TOUR PRIVATIVO": {
    "count": 4,
    "preco_medio": 541.125,
    "preco_min": 178.5,
    "preco_max": 793.0,
    "pax_medio": 4.75,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      },
      {
        "preco": 400.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      },
      {
        "preco": 793.0,
        "pax": 5,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Privativo Disp. 8 Horas"
      }
    ]
  },
  "PRIVATIVO PÃO": {
    "count": 2,
    "preco_medio": 289.25,
    "preco_min": 178.5,
    "preco_max": 400.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      },
      {
        "preco": 400.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR PRIVATIVO PÃO DE AÇÚCAR C/ VISITA CENTRO RIO E CATEDRAL"
      }
    ]
  },
  "ENTRE": {
    "count": 3,
    "preco_medio": 176.33333333333334,
    "preco_min": 101.5,
    "preco_max": 326.0,
    "pax_medio": 1.3333333333333333,
    "exemplos": [
      {
        "preco": 326.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf Entre Bairros - Agente de Viagens"
      }
    ]
  },
  "BAIRROS": {
    "count": 3,
    "preco_medio": 176.33333333333334,
    "preco_min": 101.5,
    "preco_max": 326.0,
    "pax_medio": 1.3333333333333333,
    "exemplos": [
      {
        "preco": 326.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf Entre Bairros - Agente de Viagens"
      }
    ]
  },
  "TRECHO": {
    "count": 2,
    "preco_medio": 213.75,
    "preco_min": 101.5,
    "preco_max": 326.0,
    "pax_medio": 1.0,
    "exemplos": [
      {
        "preco": 326.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      }
    ]
  },
  "TRANSFER ENTRE": {
    "count": 2,
    "preco_medio": 213.75,
    "preco_min": 101.5,
    "preco_max": 326.0,
    "pax_medio": 1.0,
    "exemplos": [
      {
        "preco": 326.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      },
      {
        "preco": 101.5,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER ENTRE BAIRROS (POR VEÍCULO E POR TRECHO)"
      }
    ]
  },
  "PRIVATIVO X": {
    "count": 3,
    "preco_medio": 247.66666666666666,
    "preco_min": 81.0,
    "preco_max": 362.0,
    "pax_medio": 5.666666666666667,
    "exemplos": [
      {
        "preco": 362.0,
        "pax": 7,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Gig Privativo x Barra"
      },
      {
        "preco": 81.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Barra Privativo x SDU"
      },
      {
        "preco": 300.0,
        "pax": 8,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Privativo x SDU"
      }
    ]
  },
  "PRIVATIVO CENTRO": {
    "count": 7,
    "preco_medio": 168.85714285714286,
    "preco_min": 63.0,
    "preco_max": 310.0,
    "pax_medio": 4.142857142857143,
    "exemplos": [
      {
        "preco": 310.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Centro X GIG"
      },
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Centro  x Gig"
      },
      {
        "preco": 63.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Centro x GIG"
      }
    ]
  },
  "08HRS": {
    "count": 11,
    "preco_medio": 764.6518181818182,
    "preco_min": 481.17,
    "preco_max": 793.0,
    "pax_medio": 8.636363636363637,
    "exemplos": [
      {
        "preco": 793.0,
        "pax": 10,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR DE 08HRS"
      },
      {
        "preco": 793.0,
        "pax": 5,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 08hrs"
      },
      {
        "preco": 793.0,
        "pax": 9,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 08hrs"
      }
    ]
  },
  "PRIVATIVO_": {
    "count": 2,
    "preco_medio": 77.0,
    "preco_min": 77.0,
    "preco_max": 77.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      }
    ]
  },
  "OUT PRIVATIVO_": {
    "count": 2,
    "preco_medio": 77.0,
    "preco_min": 77.0,
    "preco_max": 77.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      }
    ]
  },
  "PRIVATIVO_ ZS": {
    "count": 2,
    "preco_medio": 77.0,
    "preco_min": 77.0,
    "preco_max": 77.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "OUT Privativo_ ZS x GIG"
      }
    ]
  },
  "06H": {
    "count": 2,
    "preco_medio": 193.75,
    "preco_min": 178.5,
    "preco_max": 209.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 178.5,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 06h"
      },
      {
        "preco": 209.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 06h"
      }
    ]
  },
  "PRIVATIVO _": {
    "count": 11,
    "preco_medio": 199.8181818181818,
    "preco_min": 77.0,
    "preco_max": 362.0,
    "pax_medio": 3.090909090909091,
    "exemplos": [
      {
        "preco": 103.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Privativo _ GIG x Barra"
      },
      {
        "preco": 310.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Privativo _ GIG x ZS"
      },
      {
        "preco": 362.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo _ Barra x GIG"
      }
    ]
  },
  "PLAZA": {
    "count": 3,
    "preco_medio": 233.83333333333334,
    "preco_min": 101.5,
    "preco_max": 300.0,
    "pax_medio": 8.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Hotel Plaza Spania x Novotel Botafogo"
      },
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      },
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      }
    ]
  },
  "06HRS": {
    "count": 8,
    "preco_medio": 707.0,
    "preco_min": 707.0,
    "preco_max": 707.0,
    "pax_medio": 6.5,
    "exemplos": [
      {
        "preco": 707.0,
        "pax": 9,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 06hrs"
      },
      {
        "preco": 707.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 06hrs Privativo"
      },
      {
        "preco": 707.0,
        "pax": 6,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour de 06hrs"
      }
    ]
  },
  "REGULAR _": {
    "count": 8,
    "preco_medio": 165.0,
    "preco_min": 77.0,
    "preco_max": 308.0,
    "pax_medio": 4.75,
    "exemplos": [
      {
        "preco": 231.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular _ ZS x GIG"
      },
      {
        "preco": 154.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "IN Regular _ GIG x ZS"
      },
      {
        "preco": 154.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Regular _ ZS x GIG"
      }
    ]
  },
  "OUR": {
    "count": 2,
    "preco_medio": 112.0,
    "preco_min": 103.0,
    "preco_max": 121.0,
    "pax_medio": 4.0,
    "exemplos": [
      {
        "preco": 103.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Our Privativo Barra x GIG"
      },
      {
        "preco": 121.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Our Regular ZS x SDU/ZS x GIG"
      }
    ]
  },
  "PRIVATIVO COPA": {
    "count": 2,
    "preco_medio": 193.5,
    "preco_min": 77.0,
    "preco_max": 310.0,
    "pax_medio": 4.0,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Copa x Gig"
      },
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Copa x Gig"
      }
    ]
  },
  "JARDIM": {
    "count": 2,
    "preco_medio": 339.5,
    "preco_min": 170.0,
    "preco_max": 509.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botânico s/ ingresso"
      },
      {
        "preco": 509.0,
        "pax": 8,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botanico s/ ingressos"
      }
    ]
  },
  "REGULAR JARDIM": {
    "count": 2,
    "preco_medio": 339.5,
    "preco_min": 170.0,
    "preco_max": 509.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botânico s/ ingresso"
      },
      {
        "preco": 509.0,
        "pax": 8,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular Jardim Botanico s/ ingressos"
      }
    ]
  },
  "SDU REGULAR": {
    "count": 2,
    "preco_medio": 88.0,
    "preco_min": 88.0,
    "preco_max": 88.0,
    "pax_medio": 4.5,
    "exemplos": [
      {
        "preco": 88.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Sdu Regular x ZSul"
      },
      {
        "preco": 88.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In SDU Regular x Z Sul"
      }
    ]
  },
  "REGULAR X": {
    "count": 2,
    "preco_medio": 88.0,
    "preco_min": 88.0,
    "preco_max": 88.0,
    "pax_medio": 4.5,
    "exemplos": [
      {
        "preco": 88.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In Sdu Regular x ZSul"
      },
      {
        "preco": 88.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In SDU Regular x Z Sul"
      }
    ]
  },
  "SOMENTE": {
    "count": 2,
    "preco_medio": 44.0,
    "preco_min": 44.0,
    "preco_max": 44.0,
    "pax_medio": 4.0,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour somente ida"
      },
      {
        "preco": 44.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour somente retorno"
      }
    ]
  },
  "IDA": {
    "count": 3,
    "preco_medio": 73.33333333333333,
    "preco_min": 44.0,
    "preco_max": 88.0,
    "pax_medio": 2.6666666666666665,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour somente ida"
      },
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Museu do Amanha REg - IDA e VOLTA"
      },
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf de Ida e Volta ao Boulevard"
      }
    ]
  },
  "TOUR SOMENTE": {
    "count": 2,
    "preco_medio": 44.0,
    "preco_min": 44.0,
    "preco_max": 44.0,
    "pax_medio": 4.0,
    "exemplos": [
      {
        "preco": 44.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour somente ida"
      },
      {
        "preco": 44.0,
        "pax": 4,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour somente retorno"
      }
    ]
  },
  "REGUAR": {
    "count": 2,
    "preco_medio": 135.375,
    "preco_min": 103.0,
    "preco_max": 167.75,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 103.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Reguar Barra x SDU"
      },
      {
        "preco": 167.75,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "Out Reguar Barra x SDU - Cortesia"
      }
    ]
  },
  "TRF": {
    "count": 4,
    "preco_medio": 224.625,
    "preco_min": 88.0,
    "preco_max": 399.0,
    "pax_medio": 5.75,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf Entre Bairros - Agente de Viagens"
      },
      {
        "preco": 310.0,
        "pax": 8,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "IN",
        "servico_completo": "Trf In Privativo GIg x  Sul"
      },
      {
        "preco": 399.0,
        "pax": 11,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf Barra x Barra"
      }
    ]
  },
  "OPERAÇÃO": {
    "count": 2,
    "preco_medio": 305.25,
    "preco_min": 101.5,
    "preco_max": 509.0,
    "pax_medio": 6.5,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Operação nossa Tur - Cortersia Azul"
      },
      {
        "preco": 509.0,
        "pax": 11,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Reg. Corcovado - dur 04hrs Operação Interna"
      }
    ]
  },
  "REG": {
    "count": 3,
    "preco_medio": 228.33333333333334,
    "preco_min": 88.0,
    "preco_max": 509.0,
    "pax_medio": 5.666666666666667,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 11,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Reg. Corcovado - dur 04hrs Operação Interna"
      },
      {
        "preco": 88.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "SDU",
        "direcao": "N/A",
        "servico_completo": "In SDU Reg x ZSul"
      },
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Museu do Amanha REg - IDA e VOLTA"
      }
    ]
  },
  "DUR": {
    "count": 2,
    "preco_medio": 339.5,
    "preco_min": 170.0,
    "preco_max": 509.0,
    "pax_medio": 6.5,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 11,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Reg. Corcovado - dur 04hrs Operação Interna"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular - dur 04hs"
      }
    ]
  },
  "NITEROI": {
    "count": 3,
    "preco_medio": 509.0,
    "preco_min": 509.0,
    "preco_max": 509.0,
    "pax_medio": 5.666666666666667,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Niteroi x Gig"
      },
      {
        "preco": 509.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Niteroi x Gig"
      },
      {
        "preco": 509.0,
        "pax": 9,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo GIG x Niteroi"
      }
    ]
  },
  "PRIVATIVO NITEROI": {
    "count": 2,
    "preco_medio": 509.0,
    "preco_min": 509.0,
    "preco_max": 509.0,
    "pax_medio": 4.0,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Niteroi x Gig"
      },
      {
        "preco": 509.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Niteroi x Gig"
      }
    ]
  },
  "XGIG": {
    "count": 4,
    "preco_medio": 271.0,
    "preco_min": 154.0,
    "preco_max": 310.0,
    "pax_medio": 5.0,
    "exemplos": [
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul xGig"
      },
      {
        "preco": 310.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul xGig"
      },
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul xGig"
      }
    ]
  },
  "OT PRIVATIVO": {
    "count": 5,
    "preco_medio": 170.2,
    "preco_min": 77.0,
    "preco_max": 310.0,
    "pax_medio": 3.6,
    "exemplos": [
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Ot Privativo ZSul x Gig"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Ot Privativo ZSul x Gig"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Ot Privativo ZSul x Gig"
      }
    ]
  },
  "03SEDANS": {
    "count": 2,
    "preco_medio": 231.0,
    "preco_min": 231.0,
    "preco_max": 231.0,
    "pax_medio": 9.0,
    "exemplos": [
      {
        "preco": 231.0,
        "pax": 9,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gig x Zsul - 03sedans"
      },
      {
        "preco": 231.0,
        "pax": 9,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo ZSul x GIG - 03sedans"
      }
    ]
  },
  "OU REGULAR": {
    "count": 2,
    "preco_medio": 147.0,
    "preco_min": 63.0,
    "preco_max": 231.0,
    "pax_medio": 3.5,
    "exemplos": [
      {
        "preco": 63.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "CENTRO",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Ou Regular Centro x Gig"
      },
      {
        "preco": 231.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "ZONA SUL",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Ou Regular Zona Sul x Gig"
      }
    ]
  },
  "GOG": {
    "count": 3,
    "preco_medio": 180.33333333333334,
    "preco_min": 77.0,
    "preco_max": 310.0,
    "pax_medio": 4.333333333333333,
    "exemplos": [
      {
        "preco": 154.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x Zsul - 02 sedans"
      },
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x ZSul"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x ZSul"
      }
    ]
  },
  "PRIVATIVO GOG": {
    "count": 3,
    "preco_medio": 180.33333333333334,
    "preco_min": 77.0,
    "preco_max": 310.0,
    "pax_medio": 4.333333333333333,
    "exemplos": [
      {
        "preco": 154.0,
        "pax": 5,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x Zsul - 02 sedans"
      },
      {
        "preco": 310.0,
        "pax": 6,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x ZSul"
      },
      {
        "preco": 77.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "In Privativo Gog x ZSul"
      }
    ]
  },
  "REGULAR DE": {
    "count": 2,
    "preco_medio": 608.0,
    "preco_min": 509.0,
    "preco_max": 707.0,
    "pax_medio": 11.0,
    "exemplos": [
      {
        "preco": 707.0,
        "pax": 13,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular de 06hrs"
      },
      {
        "preco": 509.0,
        "pax": 9,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular de 04hrs - CCV"
      }
    ]
  },
  "WINDSOR": {
    "count": 2,
    "preco_medio": 300.0,
    "preco_min": 300.0,
    "preco_max": 300.0,
    "pax_medio": 11.0,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      },
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      }
    ]
  },
  "ATERRO": {
    "count": 2,
    "preco_medio": 300.0,
    "preco_min": 300.0,
    "preco_max": 300.0,
    "pax_medio": 11.0,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      },
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      }
    ]
  },
  "TRANSFER WINDSOR": {
    "count": 2,
    "preco_medio": 300.0,
    "preco_min": 300.0,
    "preco_max": 300.0,
    "pax_medio": 11.0,
    "exemplos": [
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      },
      {
        "preco": 300.0,
        "pax": 11,
        "tipo": "TRANSFER",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Transfer Windsor Plaza x Aterro"
      }
    ]
  },
  "ZSL": {
    "count": 2,
    "preco_medio": 309.0,
    "preco_min": 308.0,
    "preco_max": 310.0,
    "pax_medio": 10.5,
    "exemplos": [
      {
        "preco": 310.0,
        "pax": 11,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Regular Gig x ZSl"
      },
      {
        "preco": 308.0,
        "pax": 10,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Regular Gig x ZSl"
      }
    ]
  },
  "MUSEU": {
    "count": 2,
    "preco_medio": 144.0,
    "preco_min": 88.0,
    "preco_max": 200.0,
    "pax_medio": 1.5,
    "exemplos": [
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Museu do Amanha REg - IDA e VOLTA"
      },
      {
        "preco": 200.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR BOULEVARD OLÍMPICO PANORÂMICO COM VLT MUSEU DO AMANHÃ E AQUARIO"
      }
    ]
  },
  "VOLTA": {
    "count": 2,
    "preco_medio": 88.0,
    "preco_min": 88.0,
    "preco_max": 88.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Museu do Amanha REg - IDA e VOLTA"
      },
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf de Ida e Volta ao Boulevard"
      }
    ]
  },
  "PIRVATIVO": {
    "count": 2,
    "preco_medio": 232.5,
    "preco_min": 103.0,
    "preco_max": 362.0,
    "pax_medio": 2.5,
    "exemplos": [
      {
        "preco": 362.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Pirvativo Gig x Barra"
      },
      {
        "preco": 103.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Pirvativo Gig x Barra"
      }
    ]
  },
  "CCV": {
    "count": 2,
    "preco_medio": 509.0,
    "preco_min": 509.0,
    "preco_max": 509.0,
    "pax_medio": 10.0,
    "exemplos": [
      {
        "preco": 509.0,
        "pax": 11,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular CCV"
      },
      {
        "preco": 509.0,
        "pax": 9,
        "tipo": "TOUR",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Tour Regular de 04hrs - CCV"
      }
    ]
  },
  "BARRAL": {
    "count": 2,
    "preco_medio": 232.5,
    "preco_min": 103.0,
    "preco_max": 362.0,
    "pax_medio": 3.0,
    "exemplos": [
      {
        "preco": 103.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barral x Gig"
      },
      {
        "preco": 362.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barral x Gig"
      }
    ]
  },
  "PRIVATIVO BARRAL": {
    "count": 2,
    "preco_medio": 232.5,
    "preco_min": 103.0,
    "preco_max": 362.0,
    "pax_medio": 3.0,
    "exemplos": [
      {
        "preco": 103.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barral x Gig"
      },
      {
        "preco": 362.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "BARRA",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "Out Privativo Barral x Gig"
      }
    ]
  },
  "PRIVATIVA": {
    "count": 2,
    "preco_medio": 310.0,
    "preco_min": 310.0,
    "preco_max": 310.0,
    "pax_medio": 6.0,
    "exemplos": [
      {
        "preco": 310.0,
        "pax": 8,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativa Gig x ZSul"
      },
      {
        "preco": 310.0,
        "pax": 4,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "GIG",
        "direcao": "N/A",
        "servico_completo": "In Privativa Gig x ZSul"
      }
    ]
  },
  "BOULEVARD": {
    "count": 2,
    "preco_medio": 144.0,
    "preco_min": 88.0,
    "preco_max": 200.0,
    "pax_medio": 1.5,
    "exemplos": [
      {
        "preco": 200.0,
        "pax": 1,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TOUR REGULAR BOULEVARD OLÍMPICO PANORÂMICO COM VLT MUSEU DO AMANHÃ E AQUARIO"
      },
      {
        "preco": 88.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Trf de Ida e Volta ao Boulevard"
      }
    ]
  },
  "PRIVATIVO BÚZIOS": {
    "count": 2,
    "preco_medio": 160.75,
    "preco_min": 101.5,
    "preco_max": 220.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO BÚZIOS PARA AEROPORTO INTER.GALEÃO (GIG)"
      },
      {
        "preco": 220.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "TRANSFER OUT VEÍCULO PRIVATIVO BÚZIOS PARA AEROPORTO INTER.GALEÃO (GIG)"
      }
    ]
  },
  "04H": {
    "count": 2,
    "preco_medio": 135.75,
    "preco_min": 101.5,
    "preco_max": 170.0,
    "pax_medio": 2.0,
    "exemplos": [
      {
        "preco": 101.5,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 04h"
      },
      {
        "preco": 170.0,
        "pax": 2,
        "tipo": "OUTRO",
        "regiao": "N/A",
        "aeroporto": "N/A",
        "direcao": "N/A",
        "servico_completo": "Disposição 04h"
      }
    ]
  }
}

CACHE_PRECOS_HISTORICOS = {
  "TRANSFER_1pax": {
    "preco": 88.67,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_2pax": {
    "preco": 100.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_3pax": {
    "preco": 111.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_4pax": {
    "preco": 122.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_5pax": {
    "preco": 134.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_6pax": {
    "preco": 145.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_7pax": {
    "preco": 157.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_8pax": {
    "preco": 168.55,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_9pax": {
    "preco": 179.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_10pax": {
    "preco": 191.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_11pax": {
    "preco": 202.78,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_12pax": {
    "preco": 214.2,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_15pax": {
    "preco": 248.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "TRANSFER_20pax": {
    "preco": 305.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER",
    "exemplos_originais": 3
  },
  "REGULAR_1pax": {
    "preco": 109.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_2pax": {
    "preco": 120.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_3pax": {
    "preco": 130.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_4pax": {
    "preco": 140.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_5pax": {
    "preco": 150.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_6pax": {
    "preco": 160.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_7pax": {
    "preco": 170.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_8pax": {
    "preco": 181.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_9pax": {
    "preco": 191.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_10pax": {
    "preco": 201.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_11pax": {
    "preco": 211.62,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_12pax": {
    "preco": 221.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_15pax": {
    "preco": 252.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR_20pax": {
    "preco": 303.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR",
    "exemplos_originais": 3
  },
  "AEROPORTO_1pax": {
    "preco": 85.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_2pax": {
    "preco": 97.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_3pax": {
    "preco": 108.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_4pax": {
    "preco": 119.8,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_5pax": {
    "preco": 131.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_6pax": {
    "preco": 142.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_7pax": {
    "preco": 153.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_8pax": {
    "preco": 165.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_9pax": {
    "preco": 176.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_10pax": {
    "preco": 187.78,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_11pax": {
    "preco": 199.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_12pax": {
    "preco": 210.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_15pax": {
    "preco": 244.42,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "AEROPORTO_20pax": {
    "preco": 301.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "AEROPORTO",
    "exemplos_originais": 3
  },
  "SANTOS_1pax": {
    "preco": 71.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_2pax": {
    "preco": 79.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_3pax": {
    "preco": 87.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_4pax": {
    "preco": 95.28,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_5pax": {
    "preco": 103.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_6pax": {
    "preco": 111.35,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_7pax": {
    "preco": 119.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_8pax": {
    "preco": 127.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_9pax": {
    "preco": 135.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_10pax": {
    "preco": 143.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_11pax": {
    "preco": 151.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_12pax": {
    "preco": 159.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_15pax": {
    "preco": 183.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "SANTOS_20pax": {
    "preco": 223.8,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SANTOS",
    "exemplos_originais": 3
  },
  "DUMONT_1pax": {
    "preco": 71.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_2pax": {
    "preco": 79.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_3pax": {
    "preco": 87.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_4pax": {
    "preco": 95.28,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_5pax": {
    "preco": 103.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_6pax": {
    "preco": 111.35,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_7pax": {
    "preco": 119.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_8pax": {
    "preco": 127.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_9pax": {
    "preco": 135.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_10pax": {
    "preco": 143.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_11pax": {
    "preco": 151.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_12pax": {
    "preco": 159.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_15pax": {
    "preco": 183.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "DUMONT_20pax": {
    "preco": 223.8,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "DUMONT",
    "exemplos_originais": 3
  },
  "SDU_1pax": {
    "preco": 89.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_2pax": {
    "preco": 97.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_3pax": {
    "preco": 106.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_4pax": {
    "preco": 114.57,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_5pax": {
    "preco": 123.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_6pax": {
    "preco": 131.62,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_7pax": {
    "preco": 140.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_8pax": {
    "preco": 148.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_9pax": {
    "preco": 157.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_10pax": {
    "preco": 165.71,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_11pax": {
    "preco": 174.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_12pax": {
    "preco": 182.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_15pax": {
    "preco": 208.33,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "SDU_20pax": {
    "preco": 250.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SDU",
    "exemplos_originais": 3
  },
  "ZONA_1pax": {
    "preco": 86.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_2pax": {
    "preco": 96.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_3pax": {
    "preco": 106.27,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_4pax": {
    "preco": 116.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_5pax": {
    "preco": 126.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_6pax": {
    "preco": 135.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_7pax": {
    "preco": 145.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_8pax": {
    "preco": 155.62,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_9pax": {
    "preco": 165.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_10pax": {
    "preco": 175.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_11pax": {
    "preco": 185.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_12pax": {
    "preco": 195.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_15pax": {
    "preco": 224.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "ZONA_20pax": {
    "preco": 274.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZONA",
    "exemplos_originais": 3
  },
  "SUL_1pax": {
    "preco": 101.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_2pax": {
    "preco": 112.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_3pax": {
    "preco": 122.7,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_4pax": {
    "preco": 133.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_5pax": {
    "preco": 143.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_6pax": {
    "preco": 154.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_7pax": {
    "preco": 164.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_8pax": {
    "preco": 175.34,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_9pax": {
    "preco": 185.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_10pax": {
    "preco": 196.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_11pax": {
    "preco": 206.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_12pax": {
    "preco": 217.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_15pax": {
    "preco": 249.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "SUL_20pax": {
    "preco": 301.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SUL",
    "exemplos_originais": 3
  },
  "TRANSFER IN_1pax": {
    "preco": 93.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_2pax": {
    "preco": 104.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_3pax": {
    "preco": 116.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_4pax": {
    "preco": 127.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_5pax": {
    "preco": 138.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_6pax": {
    "preco": 150.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_7pax": {
    "preco": 161.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_8pax": {
    "preco": 172.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_9pax": {
    "preco": 184.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_10pax": {
    "preco": 195.33,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_11pax": {
    "preco": 206.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_12pax": {
    "preco": 217.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_15pax": {
    "preco": 251.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "TRANSFER IN_20pax": {
    "preco": 308.32,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER IN",
    "exemplos_originais": 3
  },
  "IN REGULAR_1pax": {
    "preco": 108.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_2pax": {
    "preco": 118.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_3pax": {
    "preco": 127.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_4pax": {
    "preco": 137.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_5pax": {
    "preco": 147.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_6pax": {
    "preco": 157.2,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_7pax": {
    "preco": 166.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_8pax": {
    "preco": 176.71,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_9pax": {
    "preco": 186.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_10pax": {
    "preco": 196.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_11pax": {
    "preco": 205.97,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_12pax": {
    "preco": 215.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_15pax": {
    "preco": 244.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "IN REGULAR_20pax": {
    "preco": 293.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_1pax": {
    "preco": 80.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_2pax": {
    "preco": 92.8,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_3pax": {
    "preco": 105.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_4pax": {
    "preco": 117.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_5pax": {
    "preco": 129.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_6pax": {
    "preco": 141.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_7pax": {
    "preco": 153.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_8pax": {
    "preco": 166.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_9pax": {
    "preco": 178.27,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_10pax": {
    "preco": 190.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_11pax": {
    "preco": 202.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_12pax": {
    "preco": 214.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_15pax": {
    "preco": 251.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "REGULAR AEROPORTO_20pax": {
    "preco": 312.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR AEROPORTO",
    "exemplos_originais": 3
  },
  "OUT_1pax": {
    "preco": 125.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_2pax": {
    "preco": 137.42,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_3pax": {
    "preco": 149.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_4pax": {
    "preco": 161.55,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_5pax": {
    "preco": 173.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_6pax": {
    "preco": 185.67,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_7pax": {
    "preco": 197.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_8pax": {
    "preco": 209.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_9pax": {
    "preco": 221.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_10pax": {
    "preco": 233.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_11pax": {
    "preco": 245.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_12pax": {
    "preco": 258.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_15pax": {
    "preco": 294.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "OUT_20pax": {
    "preco": 354.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT",
    "exemplos_originais": 3
  },
  "BÚZIOS_1pax": {
    "preco": 154.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_2pax": {
    "preco": 180.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_3pax": {
    "preco": 206.78,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_4pax": {
    "preco": 233.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_5pax": {
    "preco": 259.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_6pax": {
    "preco": 285.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_7pax": {
    "preco": 311.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_8pax": {
    "preco": 338.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_9pax": {
    "preco": 364.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_10pax": {
    "preco": 390.91,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_11pax": {
    "preco": 417.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_12pax": {
    "preco": 443.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_15pax": {
    "preco": 522.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "BÚZIOS_20pax": {
    "preco": 653.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BÚZIOS",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_1pax": {
    "preco": 167.56,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_2pax": {
    "preco": 191.27,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_3pax": {
    "preco": 214.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_4pax": {
    "preco": 238.7,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_5pax": {
    "preco": 262.41,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_6pax": {
    "preco": 286.12,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_7pax": {
    "preco": 309.83,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_8pax": {
    "preco": 333.54,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_9pax": {
    "preco": 357.25,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_10pax": {
    "preco": 380.97,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_11pax": {
    "preco": 404.68,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_12pax": {
    "preco": 428.39,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_15pax": {
    "preco": 499.52,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "ARMAÇÃO_20pax": {
    "preco": 618.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "ARMAÇÃO",
    "exemplos_originais": 3
  },
  "JOÃO_1pax": {
    "preco": 167.56,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_2pax": {
    "preco": 191.27,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_3pax": {
    "preco": 214.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_4pax": {
    "preco": 238.7,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_5pax": {
    "preco": 262.41,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_6pax": {
    "preco": 286.12,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_7pax": {
    "preco": 309.83,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_8pax": {
    "preco": 333.54,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_9pax": {
    "preco": 357.25,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_10pax": {
    "preco": 380.97,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_11pax": {
    "preco": 404.68,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_12pax": {
    "preco": 428.39,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_15pax": {
    "preco": 499.52,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "JOÃO_20pax": {
    "preco": 618.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "JOÃO",
    "exemplos_originais": 3
  },
  "FERNANDES_1pax": {
    "preco": 167.56,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_2pax": {
    "preco": 191.27,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_3pax": {
    "preco": 214.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_4pax": {
    "preco": 238.7,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_5pax": {
    "preco": 262.41,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_6pax": {
    "preco": 286.12,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_7pax": {
    "preco": 309.83,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_8pax": {
    "preco": 333.54,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_9pax": {
    "preco": 357.25,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_10pax": {
    "preco": 380.97,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_11pax": {
    "preco": 404.68,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_12pax": {
    "preco": 428.39,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_15pax": {
    "preco": 499.52,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "FERNANDES_20pax": {
    "preco": 618.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "FERNANDES",
    "exemplos_originais": 3
  },
  "CENTRO_1pax": {
    "preco": 91.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_2pax": {
    "preco": 101.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_3pax": {
    "preco": 110.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_4pax": {
    "preco": 120.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_5pax": {
    "preco": 130.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_6pax": {
    "preco": 140.26,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_7pax": {
    "preco": 150.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_8pax": {
    "preco": 159.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_9pax": {
    "preco": 169.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_10pax": {
    "preco": 179.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_11pax": {
    "preco": 189.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_12pax": {
    "preco": 199.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_15pax": {
    "preco": 228.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "CENTRO_20pax": {
    "preco": 277.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "CENTRO",
    "exemplos_originais": 3
  },
  "GERIBÁ_1pax": {
    "preco": 167.56,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_2pax": {
    "preco": 191.27,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_3pax": {
    "preco": 214.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_4pax": {
    "preco": 238.7,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_5pax": {
    "preco": 262.41,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_6pax": {
    "preco": 286.12,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_7pax": {
    "preco": 309.83,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_8pax": {
    "preco": 333.54,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_9pax": {
    "preco": 357.25,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_10pax": {
    "preco": 380.97,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_11pax": {
    "preco": 404.68,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_12pax": {
    "preco": 428.39,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_15pax": {
    "preco": 499.52,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "GERIBÁ_20pax": {
    "preco": 618.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "GERIBÁ",
    "exemplos_originais": 3
  },
  "INTER_1pax": {
    "preco": 92.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_2pax": {
    "preco": 105.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_3pax": {
    "preco": 118.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_4pax": {
    "preco": 131.97,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_5pax": {
    "preco": 145.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_6pax": {
    "preco": 158.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_7pax": {
    "preco": 171.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_8pax": {
    "preco": 184.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_9pax": {
    "preco": 198.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_10pax": {
    "preco": 211.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_11pax": {
    "preco": 224.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_12pax": {
    "preco": 237.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_15pax": {
    "preco": 277.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "INTER_20pax": {
    "preco": 343.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "INTER",
    "exemplos_originais": 3
  },
  "GALEÃO_1pax": {
    "preco": 92.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_2pax": {
    "preco": 105.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_3pax": {
    "preco": 118.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_4pax": {
    "preco": 131.97,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_5pax": {
    "preco": 145.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_6pax": {
    "preco": 158.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_7pax": {
    "preco": 171.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_8pax": {
    "preco": 184.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_9pax": {
    "preco": 198.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_10pax": {
    "preco": 211.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_11pax": {
    "preco": 224.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_12pax": {
    "preco": 237.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_15pax": {
    "preco": 277.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GALEÃO_20pax": {
    "preco": 343.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GALEÃO",
    "exemplos_originais": 3
  },
  "GIG_1pax": {
    "preco": 142.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_2pax": {
    "preco": 156.27,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_3pax": {
    "preco": 169.58,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_4pax": {
    "preco": 182.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_5pax": {
    "preco": 196.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_6pax": {
    "preco": 209.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_7pax": {
    "preco": 222.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_8pax": {
    "preco": 236.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_9pax": {
    "preco": 249.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_10pax": {
    "preco": 262.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_11pax": {
    "preco": 276.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_12pax": {
    "preco": 289.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_15pax": {
    "preco": 329.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "GIG_20pax": {
    "preco": 395.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "GIG",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_1pax": {
    "preco": 78.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_2pax": {
    "preco": 90.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_3pax": {
    "preco": 101.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_4pax": {
    "preco": 112.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_5pax": {
    "preco": 124.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_6pax": {
    "preco": 135.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_7pax": {
    "preco": 146.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_8pax": {
    "preco": 158.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_9pax": {
    "preco": 169.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_10pax": {
    "preco": 181.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_11pax": {
    "preco": 192.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_12pax": {
    "preco": 203.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_15pax": {
    "preco": 238.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "TRANSFER OUT_20pax": {
    "preco": 294.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TRANSFER OUT",
    "exemplos_originais": 3
  },
  "OUT REGULAR_1pax": {
    "preco": 97.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_2pax": {
    "preco": 106.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_3pax": {
    "preco": 116.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_4pax": {
    "preco": 125.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_5pax": {
    "preco": 135.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_6pax": {
    "preco": 144.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_7pax": {
    "preco": 154.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_8pax": {
    "preco": 163.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_9pax": {
    "preco": 173.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_10pax": {
    "preco": 182.86,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_11pax": {
    "preco": 192.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_12pax": {
    "preco": 201.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_15pax": {
    "preco": 230.34,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "OUT REGULAR_20pax": {
    "preco": 277.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR BÚZIOS_1pax": {
    "preco": 51.66,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_2pax": {
    "preco": 59.22,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_3pax": {
    "preco": 66.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_4pax": {
    "preco": 74.34,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_5pax": {
    "preco": 81.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_6pax": {
    "preco": 89.46,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_7pax": {
    "preco": 97.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_8pax": {
    "preco": 104.58,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_9pax": {
    "preco": 112.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_10pax": {
    "preco": 119.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_11pax": {
    "preco": 127.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_12pax": {
    "preco": 134.82,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_15pax": {
    "preco": 157.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "REGULAR BÚZIOS_20pax": {
    "preco": 195.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR BÚZIOS",
    "exemplos_originais": 2
  },
  "VEÍCULO_1pax": {
    "preco": 103.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_2pax": {
    "preco": 115.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_3pax": {
    "preco": 127.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_4pax": {
    "preco": 138.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_5pax": {
    "preco": 150.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_6pax": {
    "preco": 162.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_7pax": {
    "preco": 174.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_8pax": {
    "preco": 186.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_9pax": {
    "preco": 198.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_10pax": {
    "preco": 209.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_11pax": {
    "preco": 221.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_12pax": {
    "preco": 233.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_15pax": {
    "preco": 269.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "VEÍCULO_20pax": {
    "preco": 328.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_1pax": {
    "preco": 156.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_2pax": {
    "preco": 171.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_3pax": {
    "preco": 185.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_4pax": {
    "preco": 200.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_5pax": {
    "preco": 214.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_6pax": {
    "preco": 229.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_7pax": {
    "preco": 243.7,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_8pax": {
    "preco": 258.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_9pax": {
    "preco": 272.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_10pax": {
    "preco": 287.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_11pax": {
    "preco": 301.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_12pax": {
    "preco": 316.15,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_15pax": {
    "preco": 359.62,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO_20pax": {
    "preco": 432.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_1pax": {
    "preco": 91.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_2pax": {
    "preco": 102.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_3pax": {
    "preco": 112.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_4pax": {
    "preco": 123.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_5pax": {
    "preco": 134.15,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_6pax": {
    "preco": 144.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_7pax": {
    "preco": 155.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_8pax": {
    "preco": 165.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_9pax": {
    "preco": 176.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_10pax": {
    "preco": 187.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_11pax": {
    "preco": 197.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_12pax": {
    "preco": 208.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_15pax": {
    "preco": 239.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "VEÍCULO PRIVATIVO_20pax": {
    "preco": 292.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "VEÍCULO PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_1pax": {
    "preco": 79.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_2pax": {
    "preco": 88.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_3pax": {
    "preco": 98.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_4pax": {
    "preco": 108.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_5pax": {
    "preco": 118.52,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_6pax": {
    "preco": 128.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_7pax": {
    "preco": 138.27,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_8pax": {
    "preco": 148.15,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_9pax": {
    "preco": 158.02,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_10pax": {
    "preco": 167.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_11pax": {
    "preco": 177.77,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_12pax": {
    "preco": 187.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_15pax": {
    "preco": 217.28,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZONA_20pax": {
    "preco": 266.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZONA",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_1pax": {
    "preco": 174.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_2pax": {
    "preco": 189.97,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_3pax": {
    "preco": 205.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_4pax": {
    "preco": 220.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_5pax": {
    "preco": 235.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_6pax": {
    "preco": 251.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_7pax": {
    "preco": 266.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_8pax": {
    "preco": 281.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_9pax": {
    "preco": 297.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_10pax": {
    "preco": 312.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_11pax": {
    "preco": 327.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_12pax": {
    "preco": 343.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_15pax": {
    "preco": 389.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "IN PRIVATIVO_20pax": {
    "preco": 465.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "IN PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_1pax": {
    "preco": 102.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_2pax": {
    "preco": 113.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_3pax": {
    "preco": 124.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_4pax": {
    "preco": 135.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_5pax": {
    "preco": 146.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_6pax": {
    "preco": 157.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_7pax": {
    "preco": 168.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_8pax": {
    "preco": 179.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_9pax": {
    "preco": 189.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_10pax": {
    "preco": 200.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_11pax": {
    "preco": 211.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_12pax": {
    "preco": 222.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_15pax": {
    "preco": 255.26,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "PRIVATIVO AEROPORTO_20pax": {
    "preco": 309.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO AEROPORTO",
    "exemplos_originais": 3
  },
  "BARRA_1pax": {
    "preco": 175.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_2pax": {
    "preco": 191.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_3pax": {
    "preco": 207.77,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_4pax": {
    "preco": 224.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_5pax": {
    "preco": 240.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_6pax": {
    "preco": 256.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_7pax": {
    "preco": 272.71,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_8pax": {
    "preco": 288.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_9pax": {
    "preco": 305.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_10pax": {
    "preco": 321.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_11pax": {
    "preco": 337.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_12pax": {
    "preco": 353.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_15pax": {
    "preco": 402.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "BARRA_20pax": {
    "preco": 483.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "BARRA",
    "exemplos_originais": 3
  },
  "TIJUCA_1pax": {
    "preco": 120.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_2pax": {
    "preco": 140.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_3pax": {
    "preco": 159.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_4pax": {
    "preco": 179.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_5pax": {
    "preco": 198.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_6pax": {
    "preco": 217.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_7pax": {
    "preco": 237.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_8pax": {
    "preco": 256.86,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_9pax": {
    "preco": 276.32,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_10pax": {
    "preco": 295.78,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_11pax": {
    "preco": 315.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_12pax": {
    "preco": 334.71,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_15pax": {
    "preco": 393.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "TIJUCA_20pax": {
    "preco": 490.42,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TIJUCA",
    "exemplos_originais": 3
  },
  "RECREIO_1pax": {
    "preco": 90.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_2pax": {
    "preco": 104.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_3pax": {
    "preco": 118.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_4pax": {
    "preco": 132.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_5pax": {
    "preco": 146.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_6pax": {
    "preco": 161.15,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_7pax": {
    "preco": 175.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_8pax": {
    "preco": 189.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_9pax": {
    "preco": 203.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_10pax": {
    "preco": 217.77,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_11pax": {
    "preco": 231.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_12pax": {
    "preco": 246.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_15pax": {
    "preco": 288.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "RECREIO_20pax": {
    "preco": 359.32,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "RECREIO",
    "exemplos_originais": 3
  },
  "DOS_1pax": {
    "preco": 112.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_2pax": {
    "preco": 125.31,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_3pax": {
    "preco": 138.55,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_4pax": {
    "preco": 151.79,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_5pax": {
    "preco": 165.03,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_6pax": {
    "preco": 178.26,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_7pax": {
    "preco": 191.5,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_8pax": {
    "preco": 204.74,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_9pax": {
    "preco": 217.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_10pax": {
    "preco": 231.21,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_11pax": {
    "preco": 244.45,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_12pax": {
    "preco": 257.69,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_15pax": {
    "preco": 297.4,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "DOS_20pax": {
    "preco": 363.59,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "DOS",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_1pax": {
    "preco": 112.08,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_2pax": {
    "preco": 125.31,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_3pax": {
    "preco": 138.55,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_4pax": {
    "preco": 151.79,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_5pax": {
    "preco": 165.03,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_6pax": {
    "preco": 178.26,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_7pax": {
    "preco": 191.5,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_8pax": {
    "preco": 204.74,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_9pax": {
    "preco": 217.98,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_10pax": {
    "preco": 231.21,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_11pax": {
    "preco": 244.45,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_12pax": {
    "preco": 257.69,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_15pax": {
    "preco": 297.4,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "BANDEIRANTES_20pax": {
    "preco": 363.59,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "BANDEIRANTES",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_1pax": {
    "preco": 115.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_2pax": {
    "preco": 129.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_3pax": {
    "preco": 142.2,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_4pax": {
    "preco": 155.35,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_5pax": {
    "preco": 168.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_6pax": {
    "preco": 181.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_7pax": {
    "preco": 194.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_8pax": {
    "preco": 207.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_9pax": {
    "preco": 221.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_10pax": {
    "preco": 234.26,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_11pax": {
    "preco": 247.42,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_12pax": {
    "preco": 260.57,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_15pax": {
    "preco": 300.02,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "REGULAR BARRA_20pax": {
    "preco": 365.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR BARRA",
    "exemplos_originais": 3
  },
  "HOTÉIS_1pax": {
    "preco": 60.03,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_2pax": {
    "preco": 69.73,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_3pax": {
    "preco": 79.44,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_4pax": {
    "preco": 89.14,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_5pax": {
    "preco": 98.85,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_6pax": {
    "preco": 108.55,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_7pax": {
    "preco": 118.26,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_8pax": {
    "preco": 127.96,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_9pax": {
    "preco": 137.67,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_10pax": {
    "preco": 147.37,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_11pax": {
    "preco": 157.08,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_12pax": {
    "preco": 166.78,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_15pax": {
    "preco": 195.9,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "HOTÉIS_20pax": {
    "preco": 244.42,
    "confianca": 0.9,
    "fonte": "historico",
    "base_palavra": "HOTÉIS",
    "exemplos_originais": 3
  },
  "ZSUL_1pax": {
    "preco": 135.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_2pax": {
    "preco": 148.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_3pax": {
    "preco": 160.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_4pax": {
    "preco": 172.02,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_5pax": {
    "preco": 184.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_6pax": {
    "preco": 196.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_7pax": {
    "preco": 208.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_8pax": {
    "preco": 220.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_9pax": {
    "preco": 232.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_10pax": {
    "preco": 244.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_11pax": {
    "preco": 256.09,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_12pax": {
    "preco": 268.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_15pax": {
    "preco": 304.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "ZSUL_20pax": {
    "preco": 364.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "ZSUL",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_1pax": {
    "preco": 155.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_2pax": {
    "preco": 169.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_3pax": {
    "preco": 183.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_4pax": {
    "preco": 197.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_5pax": {
    "preco": 211.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_6pax": {
    "preco": 226.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_7pax": {
    "preco": 240.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_8pax": {
    "preco": 254.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_9pax": {
    "preco": 268.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_10pax": {
    "preco": 282.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_11pax": {
    "preco": 296.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_12pax": {
    "preco": 310.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_15pax": {
    "preco": 353.32,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OUT PRIVATIVO_20pax": {
    "preco": 424.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_1pax": {
    "preco": 154.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_2pax": {
    "preco": 167.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_3pax": {
    "preco": 181.2,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_4pax": {
    "preco": 194.65,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_5pax": {
    "preco": 208.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_6pax": {
    "preco": 221.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_7pax": {
    "preco": 235.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_8pax": {
    "preco": 248.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_9pax": {
    "preco": 261.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_10pax": {
    "preco": 275.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_11pax": {
    "preco": 288.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_12pax": {
    "preco": 302.28,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_15pax": {
    "preco": 342.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZSUL_20pax": {
    "preco": 409.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_1pax": {
    "preco": 176.16,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_2pax": {
    "preco": 191.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_3pax": {
    "preco": 206.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_4pax": {
    "preco": 222.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_5pax": {
    "preco": 237.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_6pax": {
    "preco": 253.08,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_7pax": {
    "preco": 268.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_8pax": {
    "preco": 283.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_9pax": {
    "preco": 299.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_10pax": {
    "preco": 314.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_11pax": {
    "preco": 330.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_12pax": {
    "preco": 345.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_15pax": {
    "preco": 391.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GIG_20pax": {
    "preco": 468.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_1pax": {
    "preco": 130.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_2pax": {
    "preco": 141.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_3pax": {
    "preco": 151.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_4pax": {
    "preco": 162.02,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_5pax": {
    "preco": 172.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_6pax": {
    "preco": 182.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_7pax": {
    "preco": 193.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_8pax": {
    "preco": 203.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_9pax": {
    "preco": 213.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_10pax": {
    "preco": 224.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_11pax": {
    "preco": 234.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_12pax": {
    "preco": 244.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_15pax": {
    "preco": 275.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "REGULAR GIG_20pax": {
    "preco": 327.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR GIG",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_1pax": {
    "preco": 122.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_2pax": {
    "preco": 135.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_3pax": {
    "preco": 148.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_4pax": {
    "preco": 161.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_5pax": {
    "preco": 173.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_6pax": {
    "preco": 186.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_7pax": {
    "preco": 199.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_8pax": {
    "preco": 212.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_9pax": {
    "preco": 225.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_10pax": {
    "preco": 237.91,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_11pax": {
    "preco": 250.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_12pax": {
    "preco": 263.53,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_15pax": {
    "preco": 301.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "PRIVATIVO ZS_20pax": {
    "preco": 365.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_1pax": {
    "preco": 102.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_2pax": {
    "preco": 111.26,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_3pax": {
    "preco": 120.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_4pax": {
    "preco": 128.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_5pax": {
    "preco": 137.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_6pax": {
    "preco": 146.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_7pax": {
    "preco": 155.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_8pax": {
    "preco": 164.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_9pax": {
    "preco": 172.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_10pax": {
    "preco": 181.74,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_11pax": {
    "preco": 190.55,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_12pax": {
    "preco": 199.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_15pax": {
    "preco": 225.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "REGULAR ZSUL_20pax": {
    "preco": 269.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZSUL",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_1pax": {
    "preco": 156.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_2pax": {
    "preco": 169.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_3pax": {
    "preco": 183.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_4pax": {
    "preco": 196.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_5pax": {
    "preco": 209.91,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_6pax": {
    "preco": 223.33,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_7pax": {
    "preco": 236.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_8pax": {
    "preco": 250.17,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_9pax": {
    "preco": 263.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_10pax": {
    "preco": 277.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_11pax": {
    "preco": 290.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_12pax": {
    "preco": 303.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_15pax": {
    "preco": 344.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO SDU_20pax": {
    "preco": 411.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO SDU",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_1pax": {
    "preco": 206.39,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_2pax": {
    "preco": 223.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_3pax": {
    "preco": 240.46,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_4pax": {
    "preco": 257.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_5pax": {
    "preco": 274.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_6pax": {
    "preco": 291.57,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_7pax": {
    "preco": 308.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_8pax": {
    "preco": 325.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_9pax": {
    "preco": 342.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_10pax": {
    "preco": 359.72,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_11pax": {
    "preco": 376.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_12pax": {
    "preco": 393.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_15pax": {
    "preco": 444.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "PRIVATIVO BARRA_20pax": {
    "preco": 530.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_1pax": {
    "preco": 79.09,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_2pax": {
    "preco": 90.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_3pax": {
    "preco": 101.52,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_4pax": {
    "preco": 112.73,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_5pax": {
    "preco": 123.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_6pax": {
    "preco": 135.16,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_7pax": {
    "preco": 146.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_8pax": {
    "preco": 157.58,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_9pax": {
    "preco": 168.79,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_10pax": {
    "preco": 180.01,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_11pax": {
    "preco": 191.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_12pax": {
    "preco": 202.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_15pax": {
    "preco": 236.07,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZONA_20pax": {
    "preco": 292.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZONA",
    "exemplos_originais": 3
  },
  "REGULAR ZS_1pax": {
    "preco": 106.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_2pax": {
    "preco": 115.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_3pax": {
    "preco": 125.16,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_4pax": {
    "preco": 134.34,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_5pax": {
    "preco": 143.52,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_6pax": {
    "preco": 152.7,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_7pax": {
    "preco": 161.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_8pax": {
    "preco": 171.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_9pax": {
    "preco": 180.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_10pax": {
    "preco": 189.41,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_11pax": {
    "preco": 198.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_12pax": {
    "preco": 207.77,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_15pax": {
    "preco": 235.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "REGULAR ZS_20pax": {
    "preco": 281.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR ZS",
    "exemplos_originais": 3
  },
  "TOUR_1pax": {
    "preco": 360.35,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_2pax": {
    "preco": 385.18,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_3pax": {
    "preco": 410.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_4pax": {
    "preco": 434.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_5pax": {
    "preco": 459.64,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_6pax": {
    "preco": 484.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_7pax": {
    "preco": 509.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_8pax": {
    "preco": 534.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_9pax": {
    "preco": 558.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_10pax": {
    "preco": 583.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_11pax": {
    "preco": 608.58,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_12pax": {
    "preco": 633.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_15pax": {
    "preco": 707.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "TOUR_20pax": {
    "preco": 831.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR",
    "exemplos_originais": 3
  },
  "04HRS_1pax": {
    "preco": 278.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_2pax": {
    "preco": 299.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_3pax": {
    "preco": 320.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_4pax": {
    "preco": 341.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_5pax": {
    "preco": 362.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_6pax": {
    "preco": 382.96,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_7pax": {
    "preco": 403.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_8pax": {
    "preco": 424.7,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_9pax": {
    "preco": 445.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_10pax": {
    "preco": 466.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_11pax": {
    "preco": 487.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_12pax": {
    "preco": 508.16,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_15pax": {
    "preco": 570.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "04HRS_20pax": {
    "preco": 675.1,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "04HRS",
    "exemplos_originais": 3
  },
  "CORCOVADO_1pax": {
    "preco": 313.28,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_2pax": {
    "preco": 329.44,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_3pax": {
    "preco": 345.61,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_4pax": {
    "preco": 361.78,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_5pax": {
    "preco": 377.95,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_6pax": {
    "preco": 394.12,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_7pax": {
    "preco": 410.29,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_8pax": {
    "preco": 426.46,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_9pax": {
    "preco": 442.63,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_10pax": {
    "preco": 458.8,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_11pax": {
    "preco": 474.97,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_12pax": {
    "preco": 491.13,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_15pax": {
    "preco": 539.64,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "CORCOVADO_20pax": {
    "preco": 620.49,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "CORCOVADO",
    "exemplos_originais": 3
  },
  "TOUR DE_1pax": {
    "preco": 442.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_2pax": {
    "preco": 471.13,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_3pax": {
    "preco": 499.34,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_4pax": {
    "preco": 527.55,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_5pax": {
    "preco": 555.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_6pax": {
    "preco": 583.98,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_7pax": {
    "preco": 612.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_8pax": {
    "preco": 640.4,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_9pax": {
    "preco": 668.61,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_10pax": {
    "preco": 696.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_11pax": {
    "preco": 725.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_12pax": {
    "preco": 753.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_15pax": {
    "preco": 837.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "TOUR DE_20pax": {
    "preco": 978.93,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR DE",
    "exemplos_originais": 3
  },
  "CORCOVADO REGULAR_1pax": {
    "preco": 371.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_2pax": {
    "preco": 386.84,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_3pax": {
    "preco": 402.11,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_4pax": {
    "preco": 417.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_5pax": {
    "preco": 432.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_6pax": {
    "preco": 447.92,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_7pax": {
    "preco": 463.19,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_8pax": {
    "preco": 478.46,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_9pax": {
    "preco": 493.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_10pax": {
    "preco": 509.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_11pax": {
    "preco": 524.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_12pax": {
    "preco": 539.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_15pax": {
    "preco": 585.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "CORCOVADO REGULAR_20pax": {
    "preco": 661.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CORCOVADO REGULAR",
    "exemplos_originais": 2
  },
  "DISPOSIÇÃO_1pax": {
    "preco": 406.6,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_2pax": {
    "preco": 433.19,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_3pax": {
    "preco": 459.78,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_4pax": {
    "preco": 486.37,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_5pax": {
    "preco": 512.96,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_6pax": {
    "preco": 539.55,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_7pax": {
    "preco": 566.14,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_8pax": {
    "preco": 592.73,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_9pax": {
    "preco": 619.32,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_10pax": {
    "preco": 645.91,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_11pax": {
    "preco": 672.5,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_12pax": {
    "preco": 699.09,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_15pax": {
    "preco": 778.86,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "DISPOSIÇÃO_20pax": {
    "preco": 911.81,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "DISPOSIÇÃO",
    "exemplos_originais": 3
  },
  "HORAS_1pax": {
    "preco": 425.18,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_2pax": {
    "preco": 454.28,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_3pax": {
    "preco": 483.38,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_4pax": {
    "preco": 512.48,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_5pax": {
    "preco": 541.58,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_6pax": {
    "preco": 570.68,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_7pax": {
    "preco": 599.78,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_8pax": {
    "preco": 628.88,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_9pax": {
    "preco": 657.98,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_10pax": {
    "preco": 687.08,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_11pax": {
    "preco": 716.18,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_12pax": {
    "preco": 745.28,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_15pax": {
    "preco": 832.58,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "HORAS_20pax": {
    "preco": 978.08,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "HORAS",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_1pax": {
    "preco": 72.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_2pax": {
    "preco": 81.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_3pax": {
    "preco": 89.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_4pax": {
    "preco": 98.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_5pax": {
    "preco": 107.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_6pax": {
    "preco": 115.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_7pax": {
    "preco": 124.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_8pax": {
    "preco": 133.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_9pax": {
    "preco": 141.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_10pax": {
    "preco": 150.55,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_11pax": {
    "preco": 159.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_12pax": {
    "preco": 167.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_15pax": {
    "preco": 193.88,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR CENTRO_20pax": {
    "preco": 237.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR CENTRO",
    "exemplos_originais": 3
  },
  "REGULAR SDU_1pax": {
    "preco": 81.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_2pax": {
    "preco": 88.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_3pax": {
    "preco": 96.12,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_4pax": {
    "preco": 103.58,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_5pax": {
    "preco": 111.05,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_6pax": {
    "preco": 118.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_7pax": {
    "preco": 125.97,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_8pax": {
    "preco": 133.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_9pax": {
    "preco": 140.9,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_10pax": {
    "preco": 148.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_11pax": {
    "preco": 155.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_12pax": {
    "preco": 163.29,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_15pax": {
    "preco": 185.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "REGULAR SDU_20pax": {
    "preco": 222.99,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR SDU",
    "exemplos_originais": 3
  },
  "NOVO_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "NOVO TRANSFER_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "NOVO TRANSFER",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "TRANSFER REGULAR_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER REGULAR",
    "exemplos_originais": 2
  },
  "REGULAR IN_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "REGULAR IN_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR IN",
    "exemplos_originais": 2
  },
  "COPA_1pax": {
    "preco": 119.57,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_2pax": {
    "preco": 131.94,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_3pax": {
    "preco": 144.31,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_4pax": {
    "preco": 156.68,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_5pax": {
    "preco": 169.05,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_6pax": {
    "preco": 181.42,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_7pax": {
    "preco": 193.78,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_8pax": {
    "preco": 206.15,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_9pax": {
    "preco": 218.52,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_10pax": {
    "preco": 230.89,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_11pax": {
    "preco": 243.26,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_12pax": {
    "preco": 255.63,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_15pax": {
    "preco": 292.74,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "COPA_20pax": {
    "preco": 354.58,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "COPA",
    "exemplos_originais": 3
  },
  "DISP_1pax": {
    "preco": 383.61,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_2pax": {
    "preco": 423.76,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_3pax": {
    "preco": 463.9,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_4pax": {
    "preco": 504.05,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_5pax": {
    "preco": 544.19,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_6pax": {
    "preco": 584.34,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_7pax": {
    "preco": 624.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_8pax": {
    "preco": 664.63,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_9pax": {
    "preco": 704.78,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_10pax": {
    "preco": 744.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_11pax": {
    "preco": 785.07,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_12pax": {
    "preco": 825.21,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_15pax": {
    "preco": 945.65,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "DISP_20pax": {
    "preco": 1146.38,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DISP",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_1pax": {
    "preco": 109.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_2pax": {
    "preco": 122.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_3pax": {
    "preco": 134.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_4pax": {
    "preco": 147.47,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_5pax": {
    "preco": 160.02,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_6pax": {
    "preco": 172.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_7pax": {
    "preco": 185.11,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_8pax": {
    "preco": 197.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_9pax": {
    "preco": 210.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_10pax": {
    "preco": 222.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_11pax": {
    "preco": 235.3,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_12pax": {
    "preco": 247.85,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_15pax": {
    "preco": 285.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "PRIVATIVO Z_20pax": {
    "preco": 348.23,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO Z",
    "exemplos_originais": 3
  },
  "SEDANS_1pax": {
    "preco": 134.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_2pax": {
    "preco": 144.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_3pax": {
    "preco": 154.69,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_4pax": {
    "preco": 165.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_5pax": {
    "preco": 175.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_6pax": {
    "preco": 185.62,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_7pax": {
    "preco": 195.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_8pax": {
    "preco": 206.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_9pax": {
    "preco": 216.56,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_10pax": {
    "preco": 226.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_11pax": {
    "preco": 237.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_12pax": {
    "preco": 247.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_15pax": {
    "preco": 278.44,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "SEDANS_20pax": {
    "preco": 330.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "SEDANS",
    "exemplos_originais": 3
  },
  "DIA_1pax": {
    "preco": 269.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_2pax": {
    "preco": 284.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_3pax": {
    "preco": 298.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_4pax": {
    "preco": 313.79,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_5pax": {
    "preco": 328.65,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_6pax": {
    "preco": 343.52,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_7pax": {
    "preco": 358.38,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_8pax": {
    "preco": 373.24,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_9pax": {
    "preco": 388.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_10pax": {
    "preco": 402.97,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_11pax": {
    "preco": 417.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_12pax": {
    "preco": 432.7,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_15pax": {
    "preco": 477.29,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "DIA_20pax": {
    "preco": 551.61,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "DIA",
    "exemplos_originais": 3
  },
  "RIO_1pax": {
    "preco": 196.08,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_2pax": {
    "preco": 211.17,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_3pax": {
    "preco": 226.25,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_4pax": {
    "preco": 241.33,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_5pax": {
    "preco": 256.42,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_6pax": {
    "preco": 271.5,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_7pax": {
    "preco": 286.58,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_8pax": {
    "preco": 301.67,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_9pax": {
    "preco": 316.75,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_10pax": {
    "preco": 331.83,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_11pax": {
    "preco": 346.92,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_12pax": {
    "preco": 362.0,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_15pax": {
    "preco": 407.25,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "RIO_20pax": {
    "preco": 482.67,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "RIO",
    "exemplos_originais": 3
  },
  "PÃO_1pax": {
    "preco": 230.71,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_2pax": {
    "preco": 246.94,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_3pax": {
    "preco": 263.16,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_4pax": {
    "preco": 279.38,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_5pax": {
    "preco": 295.6,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_6pax": {
    "preco": 311.82,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_7pax": {
    "preco": 328.05,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_8pax": {
    "preco": 344.27,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_9pax": {
    "preco": 360.49,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_10pax": {
    "preco": 376.71,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_11pax": {
    "preco": 392.93,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_12pax": {
    "preco": 409.16,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_15pax": {
    "preco": 457.82,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "PÃO_20pax": {
    "preco": 538.93,
    "confianca": 0.6,
    "fonte": "historico",
    "base_palavra": "PÃO",
    "exemplos_originais": 3
  },
  "AÇÚCAR_1pax": {
    "preco": 249.23,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_2pax": {
    "preco": 264.87,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_3pax": {
    "preco": 280.52,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_4pax": {
    "preco": 296.16,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_5pax": {
    "preco": 311.8,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_6pax": {
    "preco": 327.44,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_7pax": {
    "preco": 343.09,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_8pax": {
    "preco": 358.73,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_9pax": {
    "preco": 374.37,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_10pax": {
    "preco": 390.01,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_11pax": {
    "preco": 405.65,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_12pax": {
    "preco": 421.3,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_15pax": {
    "preco": 468.22,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "AÇÚCAR_20pax": {
    "preco": 546.43,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "AÇÚCAR",
    "exemplos_originais": 3
  },
  "TREM_1pax": {
    "preco": 304.97,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_2pax": {
    "preco": 321.46,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_3pax": {
    "preco": 337.94,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_4pax": {
    "preco": 354.43,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_5pax": {
    "preco": 370.91,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_6pax": {
    "preco": 387.4,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_7pax": {
    "preco": 403.88,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_8pax": {
    "preco": 420.37,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_9pax": {
    "preco": 436.85,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_10pax": {
    "preco": 453.34,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_11pax": {
    "preco": 469.82,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_12pax": {
    "preco": 486.31,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_15pax": {
    "preco": 535.76,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "TREM_20pax": {
    "preco": 618.19,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TREM",
    "exemplos_originais": 3
  },
  "CITY_1pax": {
    "preco": 269.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_2pax": {
    "preco": 284.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_3pax": {
    "preco": 298.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_4pax": {
    "preco": 313.79,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_5pax": {
    "preco": 328.65,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_6pax": {
    "preco": 343.52,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_7pax": {
    "preco": 358.38,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_8pax": {
    "preco": 373.24,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_9pax": {
    "preco": 388.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_10pax": {
    "preco": 402.97,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_11pax": {
    "preco": 417.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_12pax": {
    "preco": 432.7,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_15pax": {
    "preco": 477.29,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "CITY_20pax": {
    "preco": 551.61,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY",
    "exemplos_originais": 3
  },
  "ALMOÇO_1pax": {
    "preco": 347.18,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_2pax": {
    "preco": 364.83,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_3pax": {
    "preco": 382.48,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_4pax": {
    "preco": 400.14,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_5pax": {
    "preco": 417.79,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_6pax": {
    "preco": 435.44,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_7pax": {
    "preco": 453.1,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_8pax": {
    "preco": 470.75,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_9pax": {
    "preco": 488.4,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_10pax": {
    "preco": 506.06,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_11pax": {
    "preco": 523.71,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_12pax": {
    "preco": 541.36,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_15pax": {
    "preco": 594.32,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "ALMOÇO_20pax": {
    "preco": 682.59,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "ALMOÇO",
    "exemplos_originais": 3
  },
  "RIO REGULAR_1pax": {
    "preco": 317.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_2pax": {
    "preco": 330.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_3pax": {
    "preco": 343.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_4pax": {
    "preco": 356.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_5pax": {
    "preco": 369.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_6pax": {
    "preco": 382.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_7pax": {
    "preco": 395.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_8pax": {
    "preco": 408.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_9pax": {
    "preco": 421.95,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_10pax": {
    "preco": 435.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_11pax": {
    "preco": 448.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_12pax": {
    "preco": 461.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_15pax": {
    "preco": 500.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "RIO REGULAR_20pax": {
    "preco": 565.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "RIO REGULAR",
    "exemplos_originais": 2
  },
  "REGULAR PÃO_1pax": {
    "preco": 256.85,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_2pax": {
    "preco": 271.03,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_3pax": {
    "preco": 285.21,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_4pax": {
    "preco": 299.39,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_5pax": {
    "preco": 313.58,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_6pax": {
    "preco": 327.76,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_7pax": {
    "preco": 341.94,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_8pax": {
    "preco": 356.12,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_9pax": {
    "preco": 370.3,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_10pax": {
    "preco": 384.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_11pax": {
    "preco": 398.67,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_12pax": {
    "preco": 412.85,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_15pax": {
    "preco": 455.39,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "REGULAR PÃO_20pax": {
    "preco": 526.3,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REGULAR PÃO",
    "exemplos_originais": 3
  },
  "CITY TOUR_1pax": {
    "preco": 269.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_2pax": {
    "preco": 284.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_3pax": {
    "preco": 298.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_4pax": {
    "preco": 313.79,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_5pax": {
    "preco": 328.65,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_6pax": {
    "preco": 343.52,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_7pax": {
    "preco": 358.38,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_8pax": {
    "preco": 373.24,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_9pax": {
    "preco": 388.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_10pax": {
    "preco": 402.97,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_11pax": {
    "preco": 417.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_12pax": {
    "preco": 432.7,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_15pax": {
    "preco": 477.29,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "CITY TOUR_20pax": {
    "preco": 551.61,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "CITY TOUR",
    "exemplos_originais": 3
  },
  "TOUR E_1pax": {
    "preco": 269.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_2pax": {
    "preco": 284.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_3pax": {
    "preco": 298.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_4pax": {
    "preco": 313.79,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_5pax": {
    "preco": 328.65,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_6pax": {
    "preco": 343.52,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_7pax": {
    "preco": 358.38,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_8pax": {
    "preco": 373.24,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_9pax": {
    "preco": 388.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_10pax": {
    "preco": 402.97,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_11pax": {
    "preco": 417.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_12pax": {
    "preco": 432.7,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_15pax": {
    "preco": 477.29,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "TOUR E_20pax": {
    "preco": 551.61,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "TOUR E",
    "exemplos_originais": 3
  },
  "SEDAN_1pax": {
    "preco": 147.33,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_2pax": {
    "preco": 175.67,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_3pax": {
    "preco": 204.0,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_4pax": {
    "preco": 232.33,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_5pax": {
    "preco": 260.67,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_6pax": {
    "preco": 289.0,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_7pax": {
    "preco": 317.33,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_8pax": {
    "preco": 345.67,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_9pax": {
    "preco": 374.0,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_10pax": {
    "preco": 402.33,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_11pax": {
    "preco": 430.67,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_12pax": {
    "preco": 459.0,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_15pax": {
    "preco": 544.0,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "SEDAN_20pax": {
    "preco": 685.67,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "SEDAN",
    "exemplos_originais": 3
  },
  "REGULAR Z_1pax": {
    "preco": 105.15,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_2pax": {
    "preco": 114.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_3pax": {
    "preco": 123.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_4pax": {
    "preco": 132.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_5pax": {
    "preco": 142.04,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_6pax": {
    "preco": 151.26,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_7pax": {
    "preco": 160.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_8pax": {
    "preco": 169.7,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_9pax": {
    "preco": 178.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_10pax": {
    "preco": 188.14,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_11pax": {
    "preco": 197.37,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_12pax": {
    "preco": 206.59,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_15pax": {
    "preco": 234.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "REGULAR Z_20pax": {
    "preco": 280.36,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "REGULAR Z",
    "exemplos_originais": 3
  },
  "VAN_1pax": {
    "preco": 373.4,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_2pax": {
    "preco": 391.66,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_3pax": {
    "preco": 409.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_4pax": {
    "preco": 428.19,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_5pax": {
    "preco": 446.45,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_6pax": {
    "preco": 464.72,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_7pax": {
    "preco": 482.98,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_8pax": {
    "preco": 501.25,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_9pax": {
    "preco": 519.51,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_10pax": {
    "preco": 537.77,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_11pax": {
    "preco": 556.04,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_12pax": {
    "preco": 574.3,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_15pax": {
    "preco": 629.09,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "VAN_20pax": {
    "preco": 720.41,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "VAN",
    "exemplos_originais": 3
  },
  "INGRESSO_1pax": {
    "preco": 219.71,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_2pax": {
    "preco": 243.67,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_3pax": {
    "preco": 267.64,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_4pax": {
    "preco": 291.61,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_5pax": {
    "preco": 315.58,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_6pax": {
    "preco": 339.54,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_7pax": {
    "preco": 363.51,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_8pax": {
    "preco": 387.48,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_9pax": {
    "preco": 411.45,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_10pax": {
    "preco": 435.42,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_11pax": {
    "preco": 459.38,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_12pax": {
    "preco": 483.35,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_15pax": {
    "preco": 555.26,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "INGRESSO_20pax": {
    "preco": 675.09,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "INGRESSO",
    "exemplos_originais": 3
  },
  "HERANÇAS_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "HERANÇAS_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "HERANÇAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "EUROPEIAS_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "EUROPEIAS",
    "exemplos_originais": 2
  },
  "PELO_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "PELO_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PELO",
    "exemplos_originais": 2
  },
  "TOUR REGULAR_1pax": {
    "preco": 261.48,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_2pax": {
    "preco": 281.16,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_3pax": {
    "preco": 300.83,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_4pax": {
    "preco": 320.51,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_5pax": {
    "preco": 340.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_6pax": {
    "preco": 359.86,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_7pax": {
    "preco": 379.54,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_8pax": {
    "preco": 399.22,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_9pax": {
    "preco": 418.89,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_10pax": {
    "preco": 438.57,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_11pax": {
    "preco": 458.25,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_12pax": {
    "preco": 477.92,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_15pax": {
    "preco": 536.95,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "TOUR REGULAR_20pax": {
    "preco": 635.33,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "TOUR REGULAR",
    "exemplos_originais": 3
  },
  "REGULAR HERANÇAS_1pax": {
    "preco": 60.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_2pax": {
    "preco": 70.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_3pax": {
    "preco": 81.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_4pax": {
    "preco": 91.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_5pax": {
    "preco": 102.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_6pax": {
    "preco": 113.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_7pax": {
    "preco": 123.81,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_8pax": {
    "preco": 134.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_9pax": {
    "preco": 145.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_10pax": {
    "preco": 155.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_11pax": {
    "preco": 166.26,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_12pax": {
    "preco": 176.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_15pax": {
    "preco": 208.71,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "REGULAR HERANÇAS_20pax": {
    "preco": 261.78,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR HERANÇAS",
    "exemplos_originais": 2
  },
  "INGRESSOS_1pax": {
    "preco": 258.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_2pax": {
    "preco": 278.39,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_3pax": {
    "preco": 298.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_4pax": {
    "preco": 319.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_5pax": {
    "preco": 339.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_6pax": {
    "preco": 359.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_7pax": {
    "preco": 380.24,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_8pax": {
    "preco": 400.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_9pax": {
    "preco": 420.98,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_10pax": {
    "preco": 441.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_11pax": {
    "preco": 461.72,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_12pax": {
    "preco": 482.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_15pax": {
    "preco": 543.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "INGRESSOS_20pax": {
    "preco": 645.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "INGRESSOS",
    "exemplos_originais": 2
  },
  "VISITA_1pax": {
    "preco": 219.83,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_2pax": {
    "preco": 237.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_3pax": {
    "preco": 254.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_4pax": {
    "preco": 271.89,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_5pax": {
    "preco": 289.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_6pax": {
    "preco": 306.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_7pax": {
    "preco": 323.96,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_8pax": {
    "preco": 341.31,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_9pax": {
    "preco": 358.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_10pax": {
    "preco": 376.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_11pax": {
    "preco": 393.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_12pax": {
    "preco": 410.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_15pax": {
    "preco": 462.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "VISITA_20pax": {
    "preco": 549.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VISITA",
    "exemplos_originais": 2
  },
  "CATEDRAL_1pax": {
    "preco": 219.83,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_2pax": {
    "preco": 237.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_3pax": {
    "preco": 254.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_4pax": {
    "preco": 271.89,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_5pax": {
    "preco": 289.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_6pax": {
    "preco": 306.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_7pax": {
    "preco": 323.96,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_8pax": {
    "preco": 341.31,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_9pax": {
    "preco": 358.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_10pax": {
    "preco": 376.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_11pax": {
    "preco": 393.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_12pax": {
    "preco": 410.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_15pax": {
    "preco": 462.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "CATEDRAL_20pax": {
    "preco": 549.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CATEDRAL",
    "exemplos_originais": 2
  },
  "TOUR PRIVATIVO_1pax": {
    "preco": 412.96,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_2pax": {
    "preco": 447.14,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_3pax": {
    "preco": 481.32,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_4pax": {
    "preco": 515.49,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_5pax": {
    "preco": 549.67,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_6pax": {
    "preco": 583.85,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_7pax": {
    "preco": 618.02,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_8pax": {
    "preco": 652.2,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_9pax": {
    "preco": 686.37,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_10pax": {
    "preco": 720.55,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_11pax": {
    "preco": 754.73,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_12pax": {
    "preco": 788.9,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_15pax": {
    "preco": 891.43,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "TOUR PRIVATIVO_20pax": {
    "preco": 1062.31,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TOUR PRIVATIVO",
    "exemplos_originais": 3
  },
  "PRIVATIVO PÃO_1pax": {
    "preco": 219.83,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_2pax": {
    "preco": 237.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_3pax": {
    "preco": 254.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_4pax": {
    "preco": 271.89,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_5pax": {
    "preco": 289.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_6pax": {
    "preco": 306.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_7pax": {
    "preco": 323.96,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_8pax": {
    "preco": 341.31,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_9pax": {
    "preco": 358.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_10pax": {
    "preco": 376.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_11pax": {
    "preco": 393.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_12pax": {
    "preco": 410.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_15pax": {
    "preco": 462.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "PRIVATIVO PÃO_20pax": {
    "preco": 549.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO PÃO",
    "exemplos_originais": 2
  },
  "ENTRE_1pax": {
    "preco": 163.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_2pax": {
    "preco": 202.78,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_3pax": {
    "preco": 242.46,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_4pax": {
    "preco": 282.13,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_5pax": {
    "preco": 321.81,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_6pax": {
    "preco": 361.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_7pax": {
    "preco": 401.16,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_8pax": {
    "preco": 440.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_9pax": {
    "preco": 480.51,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_10pax": {
    "preco": 520.18,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_11pax": {
    "preco": 559.86,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_12pax": {
    "preco": 599.53,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_15pax": {
    "preco": 718.56,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "ENTRE_20pax": {
    "preco": 916.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "ENTRE",
    "exemplos_originais": 3
  },
  "BAIRROS_1pax": {
    "preco": 163.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_2pax": {
    "preco": 202.78,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_3pax": {
    "preco": 242.46,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_4pax": {
    "preco": 282.13,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_5pax": {
    "preco": 321.81,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_6pax": {
    "preco": 361.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_7pax": {
    "preco": 401.16,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_8pax": {
    "preco": 440.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_9pax": {
    "preco": 480.51,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_10pax": {
    "preco": 520.18,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_11pax": {
    "preco": 559.86,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_12pax": {
    "preco": 599.53,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_15pax": {
    "preco": 718.56,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "BAIRROS_20pax": {
    "preco": 916.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "BAIRROS",
    "exemplos_originais": 3
  },
  "TRECHO_1pax": {
    "preco": 213.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_2pax": {
    "preco": 277.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_3pax": {
    "preco": 342.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_4pax": {
    "preco": 406.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_5pax": {
    "preco": 470.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_6pax": {
    "preco": 534.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_7pax": {
    "preco": 598.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_8pax": {
    "preco": 662.62,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_9pax": {
    "preco": 726.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_10pax": {
    "preco": 790.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_11pax": {
    "preco": 855.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_12pax": {
    "preco": 919.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_15pax": {
    "preco": 1111.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRECHO_20pax": {
    "preco": 1432.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRECHO",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_1pax": {
    "preco": 213.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_2pax": {
    "preco": 277.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_3pax": {
    "preco": 342.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_4pax": {
    "preco": 406.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_5pax": {
    "preco": 470.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_6pax": {
    "preco": 534.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_7pax": {
    "preco": 598.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_8pax": {
    "preco": 662.62,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_9pax": {
    "preco": 726.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_10pax": {
    "preco": 790.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_11pax": {
    "preco": 855.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_12pax": {
    "preco": 919.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_15pax": {
    "preco": 1111.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "TRANSFER ENTRE_20pax": {
    "preco": 1432.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER ENTRE",
    "exemplos_originais": 2
  },
  "PRIVATIVO X_1pax": {
    "preco": 186.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_2pax": {
    "preco": 199.59,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_3pax": {
    "preco": 212.7,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_4pax": {
    "preco": 225.81,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_5pax": {
    "preco": 238.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_6pax": {
    "preco": 252.04,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_7pax": {
    "preco": 265.15,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_8pax": {
    "preco": 278.26,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_9pax": {
    "preco": 291.37,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_10pax": {
    "preco": 304.48,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_11pax": {
    "preco": 317.6,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_12pax": {
    "preco": 330.71,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_15pax": {
    "preco": 370.04,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO X_20pax": {
    "preco": 435.6,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO X",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_1pax": {
    "preco": 130.43,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_2pax": {
    "preco": 142.66,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_3pax": {
    "preco": 154.88,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_4pax": {
    "preco": 167.11,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_5pax": {
    "preco": 179.34,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_6pax": {
    "preco": 191.57,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_7pax": {
    "preco": 203.79,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_8pax": {
    "preco": 216.02,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_9pax": {
    "preco": 228.25,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_10pax": {
    "preco": 240.48,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_11pax": {
    "preco": 252.7,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_12pax": {
    "preco": 264.93,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_15pax": {
    "preco": 301.61,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "PRIVATIVO CENTRO_20pax": {
    "preco": 362.75,
    "confianca": 0.7,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO CENTRO",
    "exemplos_originais": 3
  },
  "08HRS_1pax": {
    "preco": 561.82,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_2pax": {
    "preco": 588.38,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_3pax": {
    "preco": 614.94,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_4pax": {
    "preco": 641.5,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_5pax": {
    "preco": 668.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_6pax": {
    "preco": 694.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_7pax": {
    "preco": 721.19,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_8pax": {
    "preco": 747.75,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_9pax": {
    "preco": 774.31,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_10pax": {
    "preco": 800.87,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_11pax": {
    "preco": 827.43,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_12pax": {
    "preco": 854.0,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_15pax": {
    "preco": 933.68,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "08HRS_20pax": {
    "preco": 1066.49,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "08HRS",
    "exemplos_originais": 3
  },
  "PRIVATIVO__1pax": {
    "preco": 65.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__2pax": {
    "preco": 77.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__3pax": {
    "preco": 88.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__4pax": {
    "preco": 100.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__5pax": {
    "preco": 111.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__6pax": {
    "preco": 123.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__7pax": {
    "preco": 134.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__8pax": {
    "preco": 146.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__9pax": {
    "preco": 157.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__10pax": {
    "preco": 169.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__11pax": {
    "preco": 180.95,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__12pax": {
    "preco": 192.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__15pax": {
    "preco": 227.15,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO__20pax": {
    "preco": 284.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__1pax": {
    "preco": 65.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__2pax": {
    "preco": 77.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__3pax": {
    "preco": 88.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__4pax": {
    "preco": 100.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__5pax": {
    "preco": 111.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__6pax": {
    "preco": 123.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__7pax": {
    "preco": 134.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__8pax": {
    "preco": 146.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__9pax": {
    "preco": 157.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__10pax": {
    "preco": 169.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__11pax": {
    "preco": 180.95,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__12pax": {
    "preco": 192.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__15pax": {
    "preco": 227.15,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "OUT PRIVATIVO__20pax": {
    "preco": 284.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUT PRIVATIVO_",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_1pax": {
    "preco": 65.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_2pax": {
    "preco": 77.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_3pax": {
    "preco": 88.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_4pax": {
    "preco": 100.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_5pax": {
    "preco": 111.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_6pax": {
    "preco": 123.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_7pax": {
    "preco": 134.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_8pax": {
    "preco": 146.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_9pax": {
    "preco": 157.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_10pax": {
    "preco": 169.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_11pax": {
    "preco": 180.95,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_12pax": {
    "preco": 192.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_15pax": {
    "preco": 227.15,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "PRIVATIVO_ ZS_20pax": {
    "preco": 284.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO_ ZS",
    "exemplos_originais": 2
  },
  "06H_1pax": {
    "preco": 147.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_2pax": {
    "preco": 158.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_3pax": {
    "preco": 170.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_4pax": {
    "preco": 182.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_5pax": {
    "preco": 193.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_6pax": {
    "preco": 205.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_7pax": {
    "preco": 217.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_8pax": {
    "preco": 228.62,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_9pax": {
    "preco": 240.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_10pax": {
    "preco": 251.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_11pax": {
    "preco": 263.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_12pax": {
    "preco": 275.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_15pax": {
    "preco": 310.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "06H_20pax": {
    "preco": 368.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "06H",
    "exemplos_originais": 2
  },
  "PRIVATIVO __1pax": {
    "preco": 159.27,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __2pax": {
    "preco": 178.66,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __3pax": {
    "preco": 198.06,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __4pax": {
    "preco": 217.45,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __5pax": {
    "preco": 236.84,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __6pax": {
    "preco": 256.24,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __7pax": {
    "preco": 275.63,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __8pax": {
    "preco": 295.03,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __9pax": {
    "preco": 314.42,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __10pax": {
    "preco": 333.81,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __11pax": {
    "preco": 353.21,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __12pax": {
    "preco": 372.6,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __15pax": {
    "preco": 430.78,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PRIVATIVO __20pax": {
    "preco": 527.76,
    "confianca": 1.0,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO _",
    "exemplos_originais": 3
  },
  "PLAZA_1pax": {
    "preco": 172.45,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_2pax": {
    "preco": 181.22,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_3pax": {
    "preco": 189.99,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_4pax": {
    "preco": 198.76,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_5pax": {
    "preco": 207.53,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_6pax": {
    "preco": 216.3,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_7pax": {
    "preco": 225.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_8pax": {
    "preco": 233.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_9pax": {
    "preco": 242.6,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_10pax": {
    "preco": 251.37,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_11pax": {
    "preco": 260.14,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_12pax": {
    "preco": 268.91,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_15pax": {
    "preco": 295.21,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "PLAZA_20pax": {
    "preco": 339.06,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PLAZA",
    "exemplos_originais": 3
  },
  "06HRS_1pax": {
    "preco": 527.53,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_2pax": {
    "preco": 560.16,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_3pax": {
    "preco": 592.79,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_4pax": {
    "preco": 625.42,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_5pax": {
    "preco": 658.05,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_6pax": {
    "preco": 690.68,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_7pax": {
    "preco": 723.32,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_8pax": {
    "preco": 755.95,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_9pax": {
    "preco": 788.58,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_10pax": {
    "preco": 821.21,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_11pax": {
    "preco": 853.84,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_12pax": {
    "preco": 886.47,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_15pax": {
    "preco": 984.36,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "06HRS_20pax": {
    "preco": 1147.52,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "06HRS",
    "exemplos_originais": 3
  },
  "REGULAR __1pax": {
    "preco": 125.92,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __2pax": {
    "preco": 136.34,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __3pax": {
    "preco": 146.76,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __4pax": {
    "preco": 157.18,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __5pax": {
    "preco": 167.61,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __6pax": {
    "preco": 178.03,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __7pax": {
    "preco": 188.45,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __8pax": {
    "preco": 198.87,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __9pax": {
    "preco": 209.29,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __10pax": {
    "preco": 219.71,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __11pax": {
    "preco": 230.13,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __12pax": {
    "preco": 240.55,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __15pax": {
    "preco": 271.82,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "REGULAR __20pax": {
    "preco": 323.92,
    "confianca": 0.8,
    "fonte": "historico",
    "base_palavra": "REGULAR _",
    "exemplos_originais": 3
  },
  "OUR_1pax": {
    "preco": 86.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_2pax": {
    "preco": 95.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_3pax": {
    "preco": 103.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_4pax": {
    "preco": 112.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_5pax": {
    "preco": 120.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_6pax": {
    "preco": 128.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_7pax": {
    "preco": 137.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_8pax": {
    "preco": 145.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_9pax": {
    "preco": 154.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_10pax": {
    "preco": 162.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_11pax": {
    "preco": 170.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_12pax": {
    "preco": 179.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_15pax": {
    "preco": 204.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "OUR_20pax": {
    "preco": 246.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OUR",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_1pax": {
    "preco": 149.96,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_2pax": {
    "preco": 164.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_3pax": {
    "preco": 178.99,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_4pax": {
    "preco": 193.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_5pax": {
    "preco": 208.01,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_6pax": {
    "preco": 222.52,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_7pax": {
    "preco": 237.04,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_8pax": {
    "preco": 251.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_9pax": {
    "preco": 266.06,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_10pax": {
    "preco": 280.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_11pax": {
    "preco": 295.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_12pax": {
    "preco": 309.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_15pax": {
    "preco": 353.14,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "PRIVATIVO COPA_20pax": {
    "preco": 425.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO COPA",
    "exemplos_originais": 2
  },
  "JARDIM_1pax": {
    "preco": 258.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_2pax": {
    "preco": 278.39,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_3pax": {
    "preco": 298.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_4pax": {
    "preco": 319.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_5pax": {
    "preco": 339.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_6pax": {
    "preco": 359.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_7pax": {
    "preco": 380.24,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_8pax": {
    "preco": 400.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_9pax": {
    "preco": 420.98,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_10pax": {
    "preco": 441.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_11pax": {
    "preco": 461.72,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_12pax": {
    "preco": 482.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_15pax": {
    "preco": 543.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "JARDIM_20pax": {
    "preco": 645.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_1pax": {
    "preco": 258.02,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_2pax": {
    "preco": 278.39,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_3pax": {
    "preco": 298.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_4pax": {
    "preco": 319.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_5pax": {
    "preco": 339.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_6pax": {
    "preco": 359.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_7pax": {
    "preco": 380.24,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_8pax": {
    "preco": 400.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_9pax": {
    "preco": 420.98,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_10pax": {
    "preco": 441.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_11pax": {
    "preco": 461.72,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_12pax": {
    "preco": 482.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_15pax": {
    "preco": 543.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "REGULAR JARDIM_20pax": {
    "preco": 645.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR JARDIM",
    "exemplos_originais": 2
  },
  "SDU REGULAR_1pax": {
    "preco": 67.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_2pax": {
    "preco": 73.33,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_3pax": {
    "preco": 79.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_4pax": {
    "preco": 85.07,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_5pax": {
    "preco": 90.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_6pax": {
    "preco": 96.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_7pax": {
    "preco": 102.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_8pax": {
    "preco": 108.53,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_9pax": {
    "preco": 114.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_10pax": {
    "preco": 120.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_11pax": {
    "preco": 126.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_12pax": {
    "preco": 132.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_15pax": {
    "preco": 149.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "SDU REGULAR_20pax": {
    "preco": 178.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SDU REGULAR",
    "exemplos_originais": 2
  },
  "REGULAR X_1pax": {
    "preco": 67.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_2pax": {
    "preco": 73.33,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_3pax": {
    "preco": 79.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_4pax": {
    "preco": 85.07,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_5pax": {
    "preco": 90.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_6pax": {
    "preco": 96.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_7pax": {
    "preco": 102.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_8pax": {
    "preco": 108.53,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_9pax": {
    "preco": 114.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_10pax": {
    "preco": 120.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_11pax": {
    "preco": 126.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_12pax": {
    "preco": 132.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_15pax": {
    "preco": 149.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "REGULAR X_20pax": {
    "preco": 178.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR X",
    "exemplos_originais": 2
  },
  "SOMENTE_1pax": {
    "preco": 34.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_2pax": {
    "preco": 37.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_3pax": {
    "preco": 40.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_4pax": {
    "preco": 44.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_5pax": {
    "preco": 47.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_6pax": {
    "preco": 50.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_7pax": {
    "preco": 53.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_8pax": {
    "preco": 57.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_9pax": {
    "preco": 60.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_10pax": {
    "preco": 63.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_11pax": {
    "preco": 67.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_12pax": {
    "preco": 70.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_15pax": {
    "preco": 80.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "SOMENTE_20pax": {
    "preco": 96.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "SOMENTE",
    "exemplos_originais": 2
  },
  "IDA_1pax": {
    "preco": 59.58,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_2pax": {
    "preco": 67.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_3pax": {
    "preco": 76.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_4pax": {
    "preco": 84.33,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_5pax": {
    "preco": 92.58,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_6pax": {
    "preco": 100.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_7pax": {
    "preco": 109.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_8pax": {
    "preco": 117.33,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_9pax": {
    "preco": 125.58,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_10pax": {
    "preco": 133.83,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_11pax": {
    "preco": 142.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_12pax": {
    "preco": 150.33,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_15pax": {
    "preco": 175.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "IDA_20pax": {
    "preco": 216.33,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "IDA",
    "exemplos_originais": 3
  },
  "TOUR SOMENTE_1pax": {
    "preco": 34.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_2pax": {
    "preco": 37.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_3pax": {
    "preco": 40.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_4pax": {
    "preco": 44.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_5pax": {
    "preco": 47.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_6pax": {
    "preco": 50.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_7pax": {
    "preco": 53.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_8pax": {
    "preco": 57.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_9pax": {
    "preco": 60.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_10pax": {
    "preco": 63.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_11pax": {
    "preco": 67.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_12pax": {
    "preco": 70.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_15pax": {
    "preco": 80.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "TOUR SOMENTE_20pax": {
    "preco": 96.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TOUR SOMENTE",
    "exemplos_originais": 2
  },
  "REGUAR_1pax": {
    "preco": 115.07,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_2pax": {
    "preco": 135.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_3pax": {
    "preco": 155.68,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_4pax": {
    "preco": 175.99,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_5pax": {
    "preco": 196.29,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_6pax": {
    "preco": 216.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_7pax": {
    "preco": 236.91,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_8pax": {
    "preco": 257.21,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_9pax": {
    "preco": 277.52,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_10pax": {
    "preco": 297.83,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_11pax": {
    "preco": 318.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_12pax": {
    "preco": 338.44,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_15pax": {
    "preco": 399.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "REGUAR_20pax": {
    "preco": 500.89,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGUAR",
    "exemplos_originais": 2
  },
  "TRF_1pax": {
    "preco": 168.96,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_2pax": {
    "preco": 180.68,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_3pax": {
    "preco": 192.4,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_4pax": {
    "preco": 204.12,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_5pax": {
    "preco": 215.84,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_6pax": {
    "preco": 227.55,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_7pax": {
    "preco": 239.27,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_8pax": {
    "preco": 250.99,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_9pax": {
    "preco": 262.71,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_10pax": {
    "preco": 274.43,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_11pax": {
    "preco": 286.15,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_12pax": {
    "preco": 297.87,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_15pax": {
    "preco": 333.03,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "TRF_20pax": {
    "preco": 391.63,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "TRF",
    "exemplos_originais": 3
  },
  "OPERAÇÃO_1pax": {
    "preco": 227.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_2pax": {
    "preco": 241.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_3pax": {
    "preco": 255.94,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_4pax": {
    "preco": 270.03,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_5pax": {
    "preco": 284.12,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_6pax": {
    "preco": 298.21,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_7pax": {
    "preco": 312.29,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_8pax": {
    "preco": 326.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_9pax": {
    "preco": 340.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_10pax": {
    "preco": 354.56,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_11pax": {
    "preco": 368.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_12pax": {
    "preco": 382.74,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_15pax": {
    "preco": 425.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "OPERAÇÃO_20pax": {
    "preco": 495.44,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OPERAÇÃO",
    "exemplos_originais": 2
  },
  "REG_1pax": {
    "preco": 171.92,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_2pax": {
    "preco": 184.01,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_3pax": {
    "preco": 196.1,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_4pax": {
    "preco": 208.19,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_5pax": {
    "preco": 220.27,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_6pax": {
    "preco": 232.36,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_7pax": {
    "preco": 244.45,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_8pax": {
    "preco": 256.54,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_9pax": {
    "preco": 268.63,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_10pax": {
    "preco": 280.72,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_11pax": {
    "preco": 292.8,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_12pax": {
    "preco": 304.89,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_15pax": {
    "preco": 341.16,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "REG_20pax": {
    "preco": 401.6,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "REG",
    "exemplos_originais": 3
  },
  "DUR_1pax": {
    "preco": 253.32,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_2pax": {
    "preco": 268.99,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_3pax": {
    "preco": 284.66,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_4pax": {
    "preco": 300.33,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_5pax": {
    "preco": 316.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_6pax": {
    "preco": 331.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_7pax": {
    "preco": 347.33,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_8pax": {
    "preco": 363.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_9pax": {
    "preco": 378.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_10pax": {
    "preco": 394.34,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_11pax": {
    "preco": 410.01,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_12pax": {
    "preco": 425.68,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_15pax": {
    "preco": 472.69,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "DUR_20pax": {
    "preco": 551.03,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "DUR",
    "exemplos_originais": 2
  },
  "NITEROI_1pax": {
    "preco": 383.25,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_2pax": {
    "preco": 410.19,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_3pax": {
    "preco": 437.14,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_4pax": {
    "preco": 464.09,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_5pax": {
    "preco": 491.04,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_6pax": {
    "preco": 517.98,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_7pax": {
    "preco": 544.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_8pax": {
    "preco": 571.88,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_9pax": {
    "preco": 598.82,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_10pax": {
    "preco": 625.77,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_11pax": {
    "preco": 652.72,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_12pax": {
    "preco": 679.66,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_15pax": {
    "preco": 760.51,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "NITEROI_20pax": {
    "preco": 895.24,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "NITEROI",
    "exemplos_originais": 3
  },
  "PRIVATIVO NITEROI_1pax": {
    "preco": 394.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_2pax": {
    "preco": 432.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_3pax": {
    "preco": 470.82,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_4pax": {
    "preco": 509.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_5pax": {
    "preco": 547.17,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_6pax": {
    "preco": 585.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_7pax": {
    "preco": 623.53,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_8pax": {
    "preco": 661.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_9pax": {
    "preco": 699.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_10pax": {
    "preco": 738.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_11pax": {
    "preco": 776.22,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_12pax": {
    "preco": 814.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_15pax": {
    "preco": 928.92,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "PRIVATIVO NITEROI_20pax": {
    "preco": 1119.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO NITEROI",
    "exemplos_originais": 2
  },
  "XGIG_1pax": {
    "preco": 205.96,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_2pax": {
    "preco": 222.22,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_3pax": {
    "preco": 238.48,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_4pax": {
    "preco": 254.74,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_5pax": {
    "preco": 271.0,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_6pax": {
    "preco": 287.26,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_7pax": {
    "preco": 303.52,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_8pax": {
    "preco": 319.78,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_9pax": {
    "preco": 336.04,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_10pax": {
    "preco": 352.3,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_11pax": {
    "preco": 368.56,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_12pax": {
    "preco": 384.82,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_15pax": {
    "preco": 433.6,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "XGIG_20pax": {
    "preco": 514.9,
    "confianca": 0.4,
    "fonte": "historico",
    "base_palavra": "XGIG",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_1pax": {
    "preco": 133.32,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_2pax": {
    "preco": 147.51,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_3pax": {
    "preco": 161.69,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_4pax": {
    "preco": 175.87,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_5pax": {
    "preco": 190.06,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_6pax": {
    "preco": 204.24,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_7pax": {
    "preco": 218.42,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_8pax": {
    "preco": 232.61,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_9pax": {
    "preco": 246.79,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_10pax": {
    "preco": 260.97,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_11pax": {
    "preco": 275.16,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_12pax": {
    "preco": 289.34,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_15pax": {
    "preco": 331.89,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "OT PRIVATIVO_20pax": {
    "preco": 402.81,
    "confianca": 0.5,
    "fonte": "historico",
    "base_palavra": "OT PRIVATIVO",
    "exemplos_originais": 3
  },
  "03SEDANS_1pax": {
    "preco": 169.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_2pax": {
    "preco": 177.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_3pax": {
    "preco": 184.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_4pax": {
    "preco": 192.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_5pax": {
    "preco": 200.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_6pax": {
    "preco": 207.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_7pax": {
    "preco": 215.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_8pax": {
    "preco": 223.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_9pax": {
    "preco": 231.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_10pax": {
    "preco": 238.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_11pax": {
    "preco": 246.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_12pax": {
    "preco": 254.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_15pax": {
    "preco": 277.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "03SEDANS_20pax": {
    "preco": 315.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "03SEDANS",
    "exemplos_originais": 2
  },
  "OU REGULAR_1pax": {
    "preco": 115.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_2pax": {
    "preco": 128.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_3pax": {
    "preco": 140.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_4pax": {
    "preco": 153.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_5pax": {
    "preco": 165.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_6pax": {
    "preco": 178.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_7pax": {
    "preco": 191.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_8pax": {
    "preco": 203.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_9pax": {
    "preco": 216.3,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_10pax": {
    "preco": 228.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_11pax": {
    "preco": 241.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_12pax": {
    "preco": 254.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_15pax": {
    "preco": 291.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "OU REGULAR_20pax": {
    "preco": 354.9,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "OU REGULAR",
    "exemplos_originais": 2
  },
  "GOG_1pax": {
    "preco": 138.72,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_2pax": {
    "preco": 151.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_3pax": {
    "preco": 163.69,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_4pax": {
    "preco": 176.17,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_5pax": {
    "preco": 188.66,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_6pax": {
    "preco": 201.14,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_7pax": {
    "preco": 213.63,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_8pax": {
    "preco": 226.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_9pax": {
    "preco": 238.59,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_10pax": {
    "preco": 251.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_11pax": {
    "preco": 263.56,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_12pax": {
    "preco": 276.05,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_15pax": {
    "preco": 313.5,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "GOG_20pax": {
    "preco": 375.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_1pax": {
    "preco": 138.72,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_2pax": {
    "preco": 151.2,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_3pax": {
    "preco": 163.69,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_4pax": {
    "preco": 176.17,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_5pax": {
    "preco": 188.66,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_6pax": {
    "preco": 201.14,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_7pax": {
    "preco": 213.63,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_8pax": {
    "preco": 226.11,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_9pax": {
    "preco": 238.59,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_10pax": {
    "preco": 251.08,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_11pax": {
    "preco": 263.56,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_12pax": {
    "preco": 276.05,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_15pax": {
    "preco": 313.5,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "PRIVATIVO GOG_20pax": {
    "preco": 375.93,
    "confianca": 0.3,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO GOG",
    "exemplos_originais": 3
  },
  "REGULAR DE_1pax": {
    "preco": 442.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_2pax": {
    "preco": 458.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_3pax": {
    "preco": 475.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_4pax": {
    "preco": 491.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_5pax": {
    "preco": 508.51,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_6pax": {
    "preco": 525.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_7pax": {
    "preco": 541.67,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_8pax": {
    "preco": 558.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_9pax": {
    "preco": 574.84,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_10pax": {
    "preco": 591.42,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_11pax": {
    "preco": 608.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_12pax": {
    "preco": 624.58,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_15pax": {
    "preco": 674.33,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "REGULAR DE_20pax": {
    "preco": 757.24,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "REGULAR DE",
    "exemplos_originais": 2
  },
  "WINDSOR_1pax": {
    "preco": 218.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_2pax": {
    "preco": 226.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_3pax": {
    "preco": 234.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_4pax": {
    "preco": 242.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_5pax": {
    "preco": 250.91,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_6pax": {
    "preco": 259.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_7pax": {
    "preco": 267.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_8pax": {
    "preco": 275.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_9pax": {
    "preco": 283.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_10pax": {
    "preco": 291.82,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_11pax": {
    "preco": 300.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_12pax": {
    "preco": 308.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_15pax": {
    "preco": 332.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "WINDSOR_20pax": {
    "preco": 373.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "WINDSOR",
    "exemplos_originais": 2
  },
  "ATERRO_1pax": {
    "preco": 218.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_2pax": {
    "preco": 226.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_3pax": {
    "preco": 234.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_4pax": {
    "preco": 242.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_5pax": {
    "preco": 250.91,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_6pax": {
    "preco": 259.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_7pax": {
    "preco": 267.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_8pax": {
    "preco": 275.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_9pax": {
    "preco": 283.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_10pax": {
    "preco": 291.82,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_11pax": {
    "preco": 300.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_12pax": {
    "preco": 308.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_15pax": {
    "preco": 332.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "ATERRO_20pax": {
    "preco": 373.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ATERRO",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_1pax": {
    "preco": 218.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_2pax": {
    "preco": 226.36,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_3pax": {
    "preco": 234.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_4pax": {
    "preco": 242.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_5pax": {
    "preco": 250.91,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_6pax": {
    "preco": 259.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_7pax": {
    "preco": 267.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_8pax": {
    "preco": 275.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_9pax": {
    "preco": 283.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_10pax": {
    "preco": 291.82,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_11pax": {
    "preco": 300.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_12pax": {
    "preco": 308.18,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_15pax": {
    "preco": 332.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "TRANSFER WINDSOR_20pax": {
    "preco": 373.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "TRANSFER WINDSOR",
    "exemplos_originais": 2
  },
  "ZSL_1pax": {
    "preco": 225.13,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_2pax": {
    "preco": 233.96,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_3pax": {
    "preco": 242.79,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_4pax": {
    "preco": 251.61,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_5pax": {
    "preco": 260.44,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_6pax": {
    "preco": 269.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_7pax": {
    "preco": 278.1,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_8pax": {
    "preco": 286.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_9pax": {
    "preco": 295.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_10pax": {
    "preco": 304.59,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_11pax": {
    "preco": 313.41,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_12pax": {
    "preco": 322.24,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_15pax": {
    "preco": 348.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "ZSL_20pax": {
    "preco": 392.87,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "ZSL",
    "exemplos_originais": 2
  },
  "MUSEU_1pax": {
    "preco": 129.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_2pax": {
    "preco": 158.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_3pax": {
    "preco": 187.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_4pax": {
    "preco": 216.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_5pax": {
    "preco": 244.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_6pax": {
    "preco": 273.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_7pax": {
    "preco": 302.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_8pax": {
    "preco": 331.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_9pax": {
    "preco": 360.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_10pax": {
    "preco": 388.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_11pax": {
    "preco": 417.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_12pax": {
    "preco": 446.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_15pax": {
    "preco": 532.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "MUSEU_20pax": {
    "preco": 676.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "MUSEU",
    "exemplos_originais": 2
  },
  "VOLTA_1pax": {
    "preco": 74.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_2pax": {
    "preco": 88.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_3pax": {
    "preco": 101.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_4pax": {
    "preco": 114.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_5pax": {
    "preco": 127.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_6pax": {
    "preco": 140.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_7pax": {
    "preco": 154.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_8pax": {
    "preco": 167.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_9pax": {
    "preco": 180.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_10pax": {
    "preco": 193.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_11pax": {
    "preco": 206.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_12pax": {
    "preco": 220.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_15pax": {
    "preco": 259.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "VOLTA_20pax": {
    "preco": 325.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "VOLTA",
    "exemplos_originais": 2
  },
  "PIRVATIVO_1pax": {
    "preco": 190.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_2pax": {
    "preco": 218.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_3pax": {
    "preco": 246.45,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_4pax": {
    "preco": 274.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_5pax": {
    "preco": 302.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_6pax": {
    "preco": 330.15,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_7pax": {
    "preco": 358.05,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_8pax": {
    "preco": 385.95,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_9pax": {
    "preco": 413.85,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_10pax": {
    "preco": 441.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_11pax": {
    "preco": 469.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_12pax": {
    "preco": 497.55,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_15pax": {
    "preco": 581.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "PIRVATIVO_20pax": {
    "preco": 720.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PIRVATIVO",
    "exemplos_originais": 2
  },
  "CCV_1pax": {
    "preco": 371.57,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_2pax": {
    "preco": 386.84,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_3pax": {
    "preco": 402.11,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_4pax": {
    "preco": 417.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_5pax": {
    "preco": 432.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_6pax": {
    "preco": 447.92,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_7pax": {
    "preco": 463.19,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_8pax": {
    "preco": 478.46,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_9pax": {
    "preco": 493.73,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_10pax": {
    "preco": 509.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_11pax": {
    "preco": 524.27,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_12pax": {
    "preco": 539.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_15pax": {
    "preco": 585.35,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "CCV_20pax": {
    "preco": 661.7,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "CCV",
    "exemplos_originais": 2
  },
  "BARRAL_1pax": {
    "preco": 186.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_2pax": {
    "preco": 209.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_3pax": {
    "preco": 232.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_4pax": {
    "preco": 255.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_5pax": {
    "preco": 279.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_6pax": {
    "preco": 302.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_7pax": {
    "preco": 325.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_8pax": {
    "preco": 348.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_9pax": {
    "preco": 372.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_10pax": {
    "preco": 395.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_11pax": {
    "preco": 418.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_12pax": {
    "preco": 441.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_15pax": {
    "preco": 511.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "BARRAL_20pax": {
    "preco": 627.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_1pax": {
    "preco": 186.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_2pax": {
    "preco": 209.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_3pax": {
    "preco": 232.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_4pax": {
    "preco": 255.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_5pax": {
    "preco": 279.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_6pax": {
    "preco": 302.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_7pax": {
    "preco": 325.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_8pax": {
    "preco": 348.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_9pax": {
    "preco": 372.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_10pax": {
    "preco": 395.25,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_11pax": {
    "preco": 418.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_12pax": {
    "preco": 441.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_15pax": {
    "preco": 511.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVO BARRAL_20pax": {
    "preco": 627.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BARRAL",
    "exemplos_originais": 2
  },
  "PRIVATIVA_1pax": {
    "preco": 232.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_2pax": {
    "preco": 248.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_3pax": {
    "preco": 263.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_4pax": {
    "preco": 279.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_5pax": {
    "preco": 294.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_6pax": {
    "preco": 310.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_7pax": {
    "preco": 325.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_8pax": {
    "preco": 341.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_9pax": {
    "preco": 356.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_10pax": {
    "preco": 372.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_11pax": {
    "preco": 387.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_12pax": {
    "preco": 403.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_15pax": {
    "preco": 449.5,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "PRIVATIVA_20pax": {
    "preco": 527.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVA",
    "exemplos_originais": 2
  },
  "BOULEVARD_1pax": {
    "preco": 129.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_2pax": {
    "preco": 158.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_3pax": {
    "preco": 187.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_4pax": {
    "preco": 216.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_5pax": {
    "preco": 244.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_6pax": {
    "preco": 273.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_7pax": {
    "preco": 302.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_8pax": {
    "preco": 331.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_9pax": {
    "preco": 360.0,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_10pax": {
    "preco": 388.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_11pax": {
    "preco": 417.6,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_12pax": {
    "preco": 446.4,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_15pax": {
    "preco": 532.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "BOULEVARD_20pax": {
    "preco": 676.8,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "BOULEVARD",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_1pax": {
    "preco": 136.64,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_2pax": {
    "preco": 160.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_3pax": {
    "preco": 184.86,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_4pax": {
    "preco": 208.97,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_5pax": {
    "preco": 233.09,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_6pax": {
    "preco": 257.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_7pax": {
    "preco": 281.31,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_8pax": {
    "preco": 305.43,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_9pax": {
    "preco": 329.54,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_10pax": {
    "preco": 353.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_11pax": {
    "preco": 377.76,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_12pax": {
    "preco": 401.88,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_15pax": {
    "preco": 474.21,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "PRIVATIVO BÚZIOS_20pax": {
    "preco": 594.77,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "PRIVATIVO BÚZIOS",
    "exemplos_originais": 2
  },
  "04H_1pax": {
    "preco": 115.39,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_2pax": {
    "preco": 135.75,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_3pax": {
    "preco": 156.11,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_4pax": {
    "preco": 176.47,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_5pax": {
    "preco": 196.84,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_6pax": {
    "preco": 217.2,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_7pax": {
    "preco": 237.56,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_8pax": {
    "preco": 257.93,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_9pax": {
    "preco": 278.29,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_10pax": {
    "preco": 298.65,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_11pax": {
    "preco": 319.01,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_12pax": {
    "preco": 339.38,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_15pax": {
    "preco": 400.46,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  },
  "04H_20pax": {
    "preco": 502.28,
    "confianca": 0.2,
    "fonte": "historico",
    "base_palavra": "04H",
    "exemplos_originais": 2
  }
}


class BuscadorInteligenteComHistorico(BuscadorInteligentePrecosCodigoDoAnalista):
    """Versão melhorada do buscador que usa dados históricos"""
    
    def __init__(self):
        super().__init__()
        self.padroes_historicos = PADROES_HISTORICOS
        self.cache_historicos = CACHE_PRECOS_HISTORICOS
        
    def buscar_preco_com_historico(self, nome_servico, pax, numero_venda="1"):
        """Busca preço usando dados históricos primeiro, depois fallback para método original"""
        
        # Tentar busca nos dados históricos primeiro
        preco_historico = self.buscar_em_padroes_historicos(nome_servico, pax)
        
        if preco_historico:
            veiculo = self.determinar_veiculo_por_pax(pax)
            return veiculo, preco_historico, "Dados Históricos"
            
        # Fallback para método original
        return self.buscar_preco_inteligente(nome_servico, pax, numero_venda)
        
    def buscar_em_padroes_historicos(self, nome_servico, pax):
        """Busca preço nos padrões históricos"""
        if not nome_servico:
            return None
            
        texto_limpo = self.limpar_texto_servico(nome_servico)
        palavras = texto_limpo.split()
        
        melhor_preco = None
        melhor_confianca = 0
        
        # Buscar correspondências exatas no cache
        for palavra in palavras:
            chave_cache = f"{palavra}_{pax}pax"
            if chave_cache in self.cache_historicos:
                entrada = self.cache_historicos[chave_cache]
                if entrada['confianca'] > melhor_confianca:
                    melhor_preco = entrada['preco']
                    melhor_confianca = entrada['confianca']
                    
        # Buscar correspondências parciais
        if not melhor_preco:
            for palavra in palavras:
                if palavra in self.padroes_historicos:
                    dados = self.padroes_historicos[palavra]
                    # Ajustar preço baseado no PAX
                    preco_base = dados['preco_medio']
                    fator_pax = pax / max(dados['pax_medio'], 1)
                    preco_ajustado = preco_base * (0.8 + 0.2 * fator_pax)
                    
                    confianca = dados['count'] / 10
                    if confianca > melhor_confianca:
                        melhor_preco = preco_ajustado
                        melhor_confianca = confianca
                        
        return melhor_preco if melhor_confianca > 0.1 else None
        
    def limpar_texto_servico(self, texto):
        """Limpa texto do serviço (mesmo método usado na análise)"""
        if not texto:
            return ""
            
        texto = str(texto).upper()
        texto = re.sub(r'[^\w\s]', ' ', texto)
        texto = re.sub(r'\b\d+\b', '', texto)
        texto = re.sub(r'\s+', ' ', texto)
        
        return texto.strip()
        
    def determinar_veiculo_por_pax(self, pax):
        """Determina veículo baseado no PAX"""
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
            
    def obter_estatisticas_historicas(self):
        """Retorna estatísticas dos dados históricos"""
        return {
            'total_padroes': len(self.padroes_historicos),
            'total_cache': len(self.cache_historicos),
            'palavras_mais_comuns': sorted(
                [(k, v['count']) for k, v in self.padroes_historicos.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
