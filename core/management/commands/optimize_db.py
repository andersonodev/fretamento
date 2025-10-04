from django.core.management.base import BaseCommand
from django.db import connection
from core.models import Servico
from escalas.models import Escala, AlocacaoVan


class Command(BaseCommand):
    help = 'Otimiza o banco de dados (VACUUM, ANALYZE)'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            # Para SQLite
            if 'sqlite' in connection.settings_dict['ENGINE']:
                self.stdout.write('Otimizando banco SQLite...')
                cursor.execute('VACUUM;')
                cursor.execute('ANALYZE;')
                self.stdout.write(
                    self.style.SUCCESS('Banco SQLite otimizado com sucesso!')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Comando específico para SQLite')
                )
                
        # Estatísticas
        total_servicos = Servico.objects.count()
        total_escalas = Escala.objects.count()
        total_alocacoes = AlocacaoVan.objects.count()
        
        self.stdout.write(f'Estatísticas:')
        self.stdout.write(f'  - Serviços: {total_servicos}')
        self.stdout.write(f'  - Escalas: {total_escalas}')
        self.stdout.write(f'  - Alocações: {total_alocacoes}')