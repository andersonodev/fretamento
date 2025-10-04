from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.db import connection
from django.conf import settings
from core.models import Servico, ProcessamentoPlanilha
from escalas.models import Escala, AlocacaoVan
import time


class Command(BaseCommand):
    help = 'Mostra estatísticas de performance da aplicação'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== RELATÓRIO DE PERFORMANCE ===\n'))
        
        # Teste de cache
        self._test_cache_performance()
        
        # Teste de banco de dados
        self._test_database_performance()
        
        # Estatísticas gerais
        self._show_general_stats()
        
        self.stdout.write(self.style.SUCCESS('\n=== FIM DO RELATÓRIO ==='))
    
    def _test_cache_performance(self):
        self.stdout.write('📊 TESTE DE CACHE:')
        
        # Teste de escrita
        start_time = time.time()
        for i in range(100):
            cache.set(f'test_key_{i}', f'test_value_{i}', 300)
        write_time = time.time() - start_time
        
        # Teste de leitura
        start_time = time.time()
        for i in range(100):
            cache.get(f'test_key_{i}')
        read_time = time.time() - start_time
        
        # Limpeza
        for i in range(100):
            cache.delete(f'test_key_{i}')
        
        self.stdout.write(f'  ✅ Escrita: {write_time:.4f}s (100 itens)')
        self.stdout.write(f'  ✅ Leitura: {read_time:.4f}s (100 itens)')
        self.stdout.write(f'  📝 Backend: {settings.CACHES["default"]["BACKEND"]}')
        self.stdout.write('')
    
    def _test_database_performance(self):
        self.stdout.write('🗄️  TESTE DE BANCO DE DADOS:')
        
        # Teste de consulta simples
        start_time = time.time()
        count = Servico.objects.count()
        simple_query_time = time.time() - start_time
        
        # Teste de consulta complexa (como no dashboard)
        start_time = time.time()
        from django.db.models import Count, Sum
        stats = Servico.objects.aggregate(
            total=Count('id'),
            pax_total=Sum('pax')
        )
        complex_query_time = time.time() - start_time
        
        self.stdout.write(f'  ✅ Consulta simples: {simple_query_time:.4f}s')
        self.stdout.write(f'  ✅ Consulta complexa: {complex_query_time:.4f}s')
        self.stdout.write(f'  📊 Total registros: {count}')
        self.stdout.write('')
    
    def _show_general_stats(self):
        self.stdout.write('📈 ESTATÍSTICAS GERAIS:')
        
        # Contadores
        total_servicos = Servico.objects.count()
        total_escalas = Escala.objects.count()
        total_alocacoes = AlocacaoVan.objects.count()
        total_processamentos = ProcessamentoPlanilha.objects.count()
        
        # Tamanho do banco (SQLite)
        import os
        db_path = settings.DATABASES['default']['NAME']
        db_size = 0
        if os.path.exists(db_path):
            db_size = os.path.getsize(db_path) / (1024 * 1024)  # MB
        
        self.stdout.write(f'  📦 Serviços: {total_servicos:,}')
        self.stdout.write(f'  📅 Escalas: {total_escalas:,}')
        self.stdout.write(f'  🚐 Alocações: {total_alocacoes:,}')
        self.stdout.write(f'  📄 Processamentos: {total_processamentos:,}')
        self.stdout.write(f'  💾 Tamanho DB: {db_size:.2f} MB')
        
        # Índice de eficiência
        if total_servicos > 0:
            eficiencia = (total_alocacoes / total_servicos) * 100
            self.stdout.write(f'  ⚡ Eficiência: {eficiencia:.1f}%')
        
        self.stdout.write('')
        
        # Dicas de otimização
        self._show_optimization_tips(total_servicos, db_size)
    
    def _show_optimization_tips(self, total_servicos, db_size):
        self.stdout.write('💡 DICAS DE OTIMIZAÇÃO:')
        
        if total_servicos > 10000:
            self.stdout.write('  ⚠️  Considere usar PostgreSQL para melhor performance')
        
        if db_size > 100:
            self.stdout.write('  ⚠️  Banco grande - execute VACUUM regularmente')
        
        self.stdout.write('  ✅ Use cache para consultas frequentes')
        self.stdout.write('  ✅ Execute optimize_db semanalmente')
        self.stdout.write('  ✅ Monitore logs em /logs/django.log')