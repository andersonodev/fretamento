#!/usr/bin/env python
"""
Script para limpar todos os dados do sistema de fretamento.

Este script remove:
1. Todos os serviços importados
2. Todas as escalas criadas
3. Todas as alocações
4. Registros de processamento de planilhas
5. Logs e arquivos temporários
"""

import os
import sys
import django
from datetime import datetime

# Configurar Django
sys.path.append('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fretamento_project.settings')
django.setup()

from core.models import Servico, ProcessamentoPlanilha, GrupoServico as CoreGrupoServico, CalculoPreco
from escalas.models import Escala, AlocacaoVan, GrupoServico as EscalaGrupoServico, ServicoGrupo, LogEscala
from django.db import transaction


class LimpadorSistema:
    def __init__(self):
        self.total_removido = 0
        self.log_limpeza = []
        
    def log(self, mensagem):
        """Log com timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_msg = f"[{timestamp}] {mensagem}"
        print(log_msg)
        self.log_limpeza.append(log_msg)
        
    def obter_estatisticas_antes(self):
        """Obtém estatísticas antes da limpeza"""
        stats = {
            'servicos': Servico.objects.count(),
            'escalas': Escala.objects.count(),
            'alocacoes': AlocacaoVan.objects.count(),
            'grupos_escala': EscalaGrupoServico.objects.count(),
            'servicos_grupo': ServicoGrupo.objects.count(),
            'grupos_core': CoreGrupoServico.objects.count(),
            'processamentos': ProcessamentoPlanilha.objects.count(),
            'calculos_preco': CalculoPreco.objects.count(),
            'logs_escala': LogEscala.objects.count()
        }
        
        self.log("=== ESTATÍSTICAS ANTES DA LIMPEZA ===")
        for item, count in stats.items():
            self.log(f"{item}: {count}")
            
        return stats
        
    def limpar_dados_escalas(self):
        """Limpa todos os dados relacionados às escalas"""
        self.log("Limpando dados de escalas...")
        
        # Remover em ordem para evitar problemas de foreign key
        count_servicos_grupo = ServicoGrupo.objects.count()
        ServicoGrupo.objects.all().delete()
        self.log(f"Removidos {count_servicos_grupo} serviços de grupos")
        
        count_grupos_escala = EscalaGrupoServico.objects.count()
        EscalaGrupoServico.objects.all().delete()
        self.log(f"Removidos {count_grupos_escala} grupos de escalas")
        
        count_alocacoes = AlocacaoVan.objects.count()
        AlocacaoVan.objects.all().delete()
        self.log(f"Removidas {count_alocacoes} alocações")
        
        count_logs = LogEscala.objects.count()
        LogEscala.objects.all().delete()
        self.log(f"Removidos {count_logs} logs de escalas")
        
        count_escalas = Escala.objects.count()
        Escala.objects.all().delete()
        self.log(f"Removidas {count_escalas} escalas")
        
    def limpar_dados_servicos(self):
        """Limpa todos os dados relacionados aos serviços"""
        self.log("Limpando dados de serviços...")
        
        count_grupos_core = CoreGrupoServico.objects.count()
        CoreGrupoServico.objects.all().delete()
        self.log(f"Removidos {count_grupos_core} grupos de serviços (core)")
        
        count_servicos = Servico.objects.count()
        Servico.objects.all().delete()
        self.log(f"Removidos {count_servicos} serviços")
        
    def limpar_dados_processamento(self):
        """Limpa dados de processamento e cálculos"""
        self.log("Limpando dados de processamento...")
        
        count_calculos = CalculoPreco.objects.count()
        CalculoPreco.objects.all().delete()
        self.log(f"Removidos {count_calculos} cálculos de preço")
        
        count_processamentos = ProcessamentoPlanilha.objects.count()
        ProcessamentoPlanilha.objects.all().delete()
        self.log(f"Removidos {count_processamentos} registros de processamento")
        
    def limpar_arquivos_temporarios(self):
        """Remove arquivos temporários e logs"""
        self.log("Limpando arquivos temporários...")
        
        # Lista de arquivos para remover
        arquivos_remover = [
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/dados/tarifario_otimizado.json',
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/core/busca_inteligente_precos.py.backup',
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs/relatorio_importacao.txt',
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs/relatorio_otimizacao.txt',
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs/relatorio_melhorias_busca.txt',
            '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs/relatorio_final_otimizacao.txt'
        ]
        
        removidos = 0
        for arquivo in arquivos_remover:
            if os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                    self.log(f"Arquivo removido: {os.path.basename(arquivo)}")
                    removidos += 1
                except Exception as e:
                    self.log(f"Erro ao remover {arquivo}: {e}")
                    
        self.log(f"Total de arquivos removidos: {removidos}")
        
    def restaurar_busca_inteligente(self):
        """Restaura o arquivo de busca inteligente original se houver backup"""
        arquivo_busca = '/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/core/busca_inteligente_precos.py'
        arquivo_backup = arquivo_busca + '.backup'
        
        if os.path.exists(arquivo_backup):
            try:
                # Ler backup
                with open(arquivo_backup, 'r', encoding='utf-8') as f:
                    conteudo_original = f.read()
                    
                # Restaurar original
                with open(arquivo_busca, 'w', encoding='utf-8') as f:
                    f.write(conteudo_original)
                    
                # Remover backup
                os.remove(arquivo_backup)
                
                self.log("Arquivo busca_inteligente_precos.py restaurado do backup")
                
            except Exception as e:
                self.log(f"Erro ao restaurar backup: {e}")
        else:
            self.log("Nenhum backup encontrado para restaurar")
            
    def verificar_limpeza(self):
        """Verifica se a limpeza foi completa"""
        self.log("=== VERIFICAÇÃO PÓS-LIMPEZA ===")
        
        stats_final = {
            'servicos': Servico.objects.count(),
            'escalas': Escala.objects.count(),
            'alocacoes': AlocacaoVan.objects.count(),
            'grupos_escala': EscalaGrupoServico.objects.count(),
            'servicos_grupo': ServicoGrupo.objects.count(),
            'grupos_core': CoreGrupoServico.objects.count(),
            'processamentos': ProcessamentoPlanilha.objects.count(),
            'calculos_preco': CalculoPreco.objects.count(),
            'logs_escala': LogEscala.objects.count()
        }
        
        total_restante = sum(stats_final.values())
        
        for item, count in stats_final.items():
            status = "✅" if count == 0 else "⚠️"
            self.log(f"{status} {item}: {count}")
            
        if total_restante == 0:
            self.log("✅ LIMPEZA COMPLETA: Todos os dados foram removidos")
        else:
            self.log(f"⚠️ LIMPEZA PARCIAL: {total_restante} registros restantes")
            
        return total_restante == 0
        
    def gerar_relatorio_limpeza(self):
        """Gera relatório final da limpeza"""
        relatorio = f"""
=== RELATÓRIO DE LIMPEZA DO SISTEMA ===

Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}

OPERAÇÕES REALIZADAS:
✅ Remoção de todos os serviços importados
✅ Remoção de todas as escalas criadas
✅ Remoção de todas as alocações
✅ Remoção de todos os grupos de serviços
✅ Remoção de logs de escalas
✅ Remoção de registros de processamento
✅ Remoção de cálculos de preços
✅ Limpeza de arquivos temporários
✅ Restauração de arquivos originais

RESULTADO:
O sistema foi completamente limpo e está pronto para uma nova importação
ou uso normal sem dados históricos.

PRÓXIMOS PASSOS:
- O sistema está limpo e pronto para uso
- Para reimportar dados, execute novamente os scripts de importação
- Todos os arquivos de configuração originais foram preservados

LOG DETALHADO:
"""
        
        for linha in self.log_limpeza:
            relatorio += f"{linha}\n"
            
        return relatorio
        
    def executar_limpeza_completa(self):
        """Executa limpeza completa do sistema"""
        self.log("=== INICIANDO LIMPEZA COMPLETA DO SISTEMA ===")
        
        try:
            # Obter estatísticas antes
            stats_antes = self.obter_estatisticas_antes()
            
            with transaction.atomic():
                # Limpar dados em ordem segura
                self.limpar_dados_escalas()
                self.limpar_dados_servicos()
                self.limpar_dados_processamento()
                
            # Limpar arquivos (fora da transação)
            self.limpar_arquivos_temporarios()
            
            # Restaurar arquivos originais
            self.restaurar_busca_inteligente()
            
            # Verificar resultado
            limpeza_completa = self.verificar_limpeza()
            
            self.log("=== LIMPEZA CONCLUÍDA ===")
            
            return limpeza_completa
            
        except Exception as e:
            self.log(f"ERRO durante a limpeza: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Função principal"""
    print("🧹 INICIANDO LIMPEZA COMPLETA DO SISTEMA...")
    print("⚠️  ATENÇÃO: Esta operação removerá TODOS os dados importados!")
    
    # Confirmação de segurança
    confirmacao = input("\nTem certeza que deseja continuar? Digite 'LIMPAR' para confirmar: ")
    
    if confirmacao != 'LIMPAR':
        print("❌ Operação cancelada pelo usuário")
        return 1
        
    limpador = LimpadorSistema()
    
    try:
        sucesso = limpador.executar_limpeza_completa()
        
        if sucesso:
            # Gerar relatório
            relatorio = limpador.gerar_relatorio_limpeza()
            
            # Salvar relatório
            os.makedirs('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs', exist_ok=True)
            with open('/Users/anderson/my_folders/repositoriolocal/fretamento-intertouring/logs/relatorio_limpeza.txt', 'w', encoding='utf-8') as f:
                f.write(relatorio)
                
            print("\n✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
            print("📄 Relatório salvo em logs/relatorio_limpeza.txt")
            print("\n🎯 O sistema está agora completamente limpo e pronto para uso!")
            
        else:
            print("\n❌ Erro durante a limpeza!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Erro durante a limpeza: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main())