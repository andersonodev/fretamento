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
        
        # 1. Busca no TARIFARIO_JW primeiro (mais específico)
        chave_jw, preco_jw, sim_jw = self.buscar_melhor_match_tarifario(
            nome_servico, TARIFARIO_JW, threshold=0.4
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
        
        # 2. Busca no TARIFARIO_MOTORISTAS
        chave_mot, preco_mot, sim_mot = self.buscar_melhor_match_tarifario(
            nome_servico, TARIFARIO_MOTORISTAS, threshold=0.3
        )
        
        if chave_mot:
            from core.tarifarios import calcular_veiculo_recomendado
            veiculo = calcular_veiculo_recomendado(pax)
            
            # Aplica multiplicador do número de venda
            multiplicador = 1
            try:
                if numero_venda and numero_venda.strip():
                    multiplicador = int(numero_venda.strip())
            except (ValueError, TypeError):
                pass
            
            preco_final = float(preco_mot * multiplicador)
            return (veiculo, preco_final, f"Motoristas (sim: {sim_mot:.2f}, mult: {multiplicador})")
        
        # 3. Se não encontrou nada, usa preço padrão baseado no veículo
        from core.tarifarios import calcular_veiculo_recomendado
        veiculo = calcular_veiculo_recomendado(pax)
        
        precos_padrao = {
            "Executivo": 200.0,
            "Van 15 lugares": 300.0,
            "Van 18 lugares": 350.0,
            "Micro": 500.0,
            "Ônibus": 800.0
        }
        
        preco_padrao = precos_padrao.get(veiculo, 200.0)
        return (veiculo, preco_padrao, "padrão")
    
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
            numero_venda: Número de vendas para multiplicador
            
        Returns:
            Preço encontrado ou 0.0 se não encontrado
        """
        chave, preco, similaridade = self.buscar_melhor_match_tarifario(
            nome_servico, self.TARIFARIO_MOTORISTAS, threshold=0.2  # Threshold mais baixo
        )
        
        if chave and similaridade > 0.4:  # Threshold de confiança mais baixo
            multiplicador = 1
            try:
                if numero_venda and str(numero_venda).strip():
                    multiplicador = int(numero_venda.strip())
            except (ValueError, TypeError):
                pass
            
            return float(preco * multiplicador)
        
        return 0.0


# Instância global do buscador
buscador_inteligente = BuscadorInteligentePrecosCodigoDoAnalista()