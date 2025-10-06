#!/usr/bin/env python3
"""
Script para remover duplicações nas views do sistema de escalas
"""

def limpar_duplicacoes():
    views_file = '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/escalas/views.py'
    
    # Ler o arquivo
    with open(views_file, 'r', encoding='utf-8') as f:
        linhas = f.readlines()
    
    # Encontrar onde começa a segunda duplicação da função _agrupar_servicos
    inicio_duplicacao = None
    for i, linha in enumerate(linhas):
        if i > 1050 and '    def _agrupar_servicos(self, escala):' in linha:
            # Esta é a segunda definição (duplicada)
            inicio_duplicacao = i
            break
    
    if inicio_duplicacao is None:
        print("Não foi possível encontrar o início da duplicação")
        return
    
    # Encontrar onde termina a duplicação (antes da classe PuxarDadosView)
    fim_duplicacao = None
    for i, linha in enumerate(linhas[inicio_duplicacao:], inicio_duplicacao):
        if 'class PuxarDadosView(LoginRequiredMixin, View):' in linha:
            fim_duplicacao = i
            break
    
    if fim_duplicacao is None:
        print("Não foi possível encontrar o fim da duplicação")
        return
    
    print(f"Removendo linhas {inicio_duplicacao + 1} a {fim_duplicacao}")
    
    # Criar novo conteúdo sem as linhas duplicadas
    linhas_limpas = linhas[:inicio_duplicacao] + linhas[fim_duplicacao:]
    
    # Salvar arquivo limpo
    with open(views_file, 'w', encoding='utf-8') as f:
        f.writelines(linhas_limpas)
    
    print(f"✅ Duplicações removidas com sucesso!")
    print(f"   Linhas originais: {len(linhas)}")
    print(f"   Linhas após limpeza: {len(linhas_limpas)}")
    print(f"   Linhas removidas: {len(linhas) - len(linhas_limpas)}")

if __name__ == '__main__':
    limpar_duplicacoes()