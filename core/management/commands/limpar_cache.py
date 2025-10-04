from django.core.management.base import BaseCommand
from django.core.cache import cache


class Command(BaseCommand):
    help = 'Limpa todos os caches da aplicação'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pattern',
            type=str,
            help='Padrão de chave de cache para limpar (ex: dashboard_*)',
        )

    def handle(self, *args, **options):
        pattern = options.get('pattern')
        
        if pattern:
            # Para backends que suportam delete_pattern
            try:
                deleted = cache.delete_pattern(pattern)
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Caches com padrão "{pattern}" limpos: {deleted}'
                    )
                )
            except AttributeError:
                self.stdout.write(
                    self.style.WARNING(
                        'Backend de cache não suporta delete_pattern. '
                        'Limpando todo o cache.'
                    )
                )
                cache.clear()
        else:
            # Limpa todo o cache
            cache.clear()
            self.stdout.write(
                self.style.SUCCESS('Todo o cache foi limpo com sucesso!')
            )
        
        # Estatísticas do cache
        try:
            # Testa se o cache está funcionando
            cache.set('test_key', 'test_value', 1)
            if cache.get('test_key'):
                self.stdout.write('Cache está funcionando corretamente.')
            cache.delete('test_key')
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Erro ao testar cache: {e}')
            )